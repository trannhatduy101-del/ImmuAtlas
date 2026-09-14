"""2A Vaccination rates by country and region -- Sub-Task A.

Demonstrates all five assessed SQL operations: select, filter, sort, join,
aggregate. Filters submit as a GET form so the result is bookmarkable and the
back button works, which is what lets Grace leave with one link.

The division of labour follows the project spec section 7. SQL filters, sorts, joins
and aggregates. Python validates the input before it reaches the database,
whitelists the sort column, and formats the output for reading. Nothing is
sorted or aggregated in Python.
"""

import csv
import io

from flask import Blueprint, render_template, request, Response

import db

bp = Blueprint("coverage", __name__)


# A user-chosen sort cannot be bound as a parameter, so every permitted sort is
# written out here and the request can only pick one of these keys. Each ends
# with country_name so the order is deterministic and a reload cannot reshuffle
# tied rows. "coverage_reported IS NULL" first pushes the blanks to the bottom
# in both directions, rather than letting them lead an ascending sort.
SORT_KEYS = {
    "coverage_desc": "coverage_reported IS NULL, coverage_reported DESC, country_name ASC",
    "coverage_asc":  "coverage_reported IS NULL, coverage_reported ASC,  country_name ASC",
    "gap":           "gap_to_threshold IS NULL, gap_to_threshold ASC,    country_name ASC",
    "cohort":        "target_cohort IS NULL, target_cohort DESC,         country_name ASC",
    "country":       "country_name ASC",
    "region":        "region_name ASC, country_name ASC",
}
SORT_LABELS = [
    ("coverage_desc", "Coverage, highest first"),
    ("coverage_asc",  "Coverage, lowest first"),
    ("gap",           "Furthest below the threshold first"),
    ("cohort",        "Largest birth cohort first"),
    ("country",       "Country name"),
    ("region",        "Region, then country"),
]
DEFAULT_SORT = "coverage_desc"

# the project spec 4.5: a typo in the source data, corrected for display only. Never
# rewrite the supplied table.
REGION_DISPLAY_FIX = {"Latin America & Carribean": "Latin America & Caribbean"}


def fix_region(name):
    return REGION_DISPLAY_FIX.get(name, name)


def _validate(raw, allowed, cast=str):
    """Resolve a request value against the list we actually offer.

    Returns (value, rejected). This is the safety boundary the project spec section 7
    puts in Python: a value that is not on the list never reaches the database.

    Dropping an unrecognised filter WIDENS the selection, so the fact that it
    was dropped is returned too and the page says so. Silently ignoring a filter
    is how someone reads a figure for "all years" believing they asked for one
    year -- which is exactly the mistake Grace was burned by.
    """
    if raw is None or raw == "":
        return None, False
    try:
        value = cast(raw)
    except (TypeError, ValueError):
        return None, True
    if value in allowed:
        return value, False
    return None, True


@bp.route("/coverage")
def index():
    try:
        antigens = db.query(db.load_query("filter_antigens"))
        years = db.query(db.load_query("filter_years"))
        regions = db.query(db.load_query("filter_regions"))
        countries = db.query(db.load_query("filter_countries"))
        defaults = db.query_one(db.load_query("coverage_defaults"))
    except db.DatabaseMissing as exc:
        return render_template("pages/2a_coverage.html", db_missing=str(exc)), 503

    valid_antigens = {r["antigen"] for r in antigens}
    valid_years = {r["year"] for r in years}
    valid_regions = {r["region_id"] for r in regions}
    valid_countries = {r["country_id"] for r in countries}

    # Land on a "choose your filters" prompt until the visitor actually submits
    # the form (which carries submitted=1). Nothing is pre-run, so no figure
    # appears that the visitor did not ask for. A CSV request always implies a
    # submitted selection.
    submitted = "submitted" in request.args or request.args.get("format") == "csv"
    if not submitted:
        return render_template(
            "pages/2a_coverage.html",
            db_missing=None, submitted=False,
            antigens=antigens, years=years, regions=regions, countries=countries,
            antigen=None, year=None, region=None, country=None,
            sort_active=DEFAULT_SORT, sort_labels=SORT_LABELS,
            summary=None, region_view=[], rows=[], threshold=None,
            conflict=None, rejected=[], fix_region=fix_region,
            fmt_int=db.fmt_int, fmt_big=db.fmt_big, fmt_pct=db.fmt_pct,
        )

    # An absent parameter falls back to the default; an invalid one falls back
    # to no filter. Those are different, and conflating them would silently
    # widen a selection the visitor thought was narrow.
    rejected = []

    if "antigen" in request.args:
        antigen, bad = _validate(request.args.get("antigen"), valid_antigens)
        if bad:
            rejected.append("antigen")
    else:
        antigen = defaults["default_antigen"]

    if "year" in request.args:
        year, bad = _validate(request.args.get("year"), valid_years, int)
        if bad:
            rejected.append("year")
    else:
        year = defaults["default_year"]

    region, bad = _validate(request.args.get("region"), valid_regions, int)
    if bad:
        rejected.append("region")
    country, bad = _validate(request.args.get("country"), valid_countries)
    if bad:
        rejected.append("country")

    sort = request.args.get("sort")
    order_by = db.safe_order_by(sort, SORT_KEYS, DEFAULT_SORT)
    sort_active = sort if sort in SORT_KEYS else DEFAULT_SORT
    if sort is not None and sort not in SORT_KEYS:
        rejected.append("sort order")

    params = {"antigen": antigen, "year": year,
              "region": region, "country": country}

    summary = db.query_one(db.load_query("coverage_selection_summary"), params)
    outcome = db.query_one(db.load_query("coverage_outcome"), params)
    region_rows = db.query(db.load_query("coverage_by_region"), params)
    # The only concatenation allowed near SQL in this project. order_by can only
    # be one of the literal strings in SORT_KEYS.
    rows = db.query(db.load_query("coverage_by_country") + " ORDER BY " + order_by,
                    params)

    # Paginate the country table: 8 rows a page, navigated by a ?page= GET link
    # so it works without JavaScript and stays bookmarkable. The full `rows` is
    # kept (the CSV export needs every row); only the displayed slice is paged.
    PER_PAGE = 8
    total_rows = len(rows)
    total_pages = max(1, -(-total_rows // PER_PAGE))
    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    page = max(1, min(page, total_pages))
    page_start = (page - 1) * PER_PAGE
    page_rows = rows[page_start:page_start + PER_PAGE]
    page_from = page_start + 1 if total_rows else 0
    page_to = min(page_start + PER_PAGE, total_rows)

    threshold = None
    if antigen:
        threshold = db.query_one(db.load_query("threshold_for_antigen"),
                                 {"antigen": antigen})

    # Is the selected country actually in the selected region? If not the result
    # is legitimately empty, and the page must say why rather than showing a
    # blank table (the project spec section 8: every filter combination has a defined
    # empty state).
    conflict = None
    if country and region:
        picked = next((c for c in countries if c["country_id"] == country), None)
        if picked and picked["region_id"] != region:
            region_name = next((r["region_name"] for r in regions
                                if r["region_id"] == region), "that region")
            conflict = {
                "country": picked["country_name"],
                "country_region": fix_region(picked["region_name"]) or "no region",
                "region": fix_region(region_name),
            }

    # Bars are drawn as a percentage width. Turning a rate into a width is
    # display formatting, so it belongs here and not in the SQL.
    region_view = []
    for r in region_rows:
        weighted = r["avg_weighted"]
        region_view.append({
            "row": r,
            "name": fix_region(r["region_name"]),
            "bar_pct": min(100.0, float(weighted)) if weighted is not None else 0.0,
        })

    # CSV export of the country table exactly as filtered and sorted, so a
    # reader can take the numbers away and check them.
    if request.args.get("format") == "csv":
        return _csv_coverage(rows, antigen, year)

    return render_template(
        "pages/2a_coverage.html",
        db_missing=None, submitted=True,
        antigens=antigens, years=years, regions=regions, countries=countries,
        antigen=antigen, year=year, region=region, country=country,
        sort_active=sort_active, sort_labels=SORT_LABELS,
        summary=summary, outcome=outcome, region_view=region_view, rows=rows,
        page_rows=page_rows, page=page, total_pages=total_pages,
        total_rows=total_rows, page_from=page_from, page_to=page_to,
        threshold=threshold, conflict=conflict, rejected=rejected,
        fix_region=fix_region,
        fmt_int=db.fmt_int, fmt_big=db.fmt_big, fmt_pct=db.fmt_pct,
    )


def _csv_coverage(rows, antigen, year):
    """Stream the country table as CSV, matching what is shown on the page."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["country", "region", "coverage_reported",
                "gap_to_threshold_pp", "target_cohort",
                "doses_per_100_population", "herd_immunity_status",
                "unmatched_territory"])
    for r in rows:
        w.writerow([r["country_name"], fix_region(r["region_name"]),
                    r["coverage_reported"], r["gap_to_threshold"],
                    r["target_cohort"], r["doses_per_100_population"],
                    r["herd_immunity_status"],
                    1 if r["unmatched_territory"] else 0])
    fname = "coverage_%s_%s.csv" % (antigen or "all", year or "all")
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=%s" % fname})
