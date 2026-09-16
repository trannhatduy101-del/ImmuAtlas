"""2A Vaccination rates by country and region -- Sub-Task A.

Demonstrates all five assessed SQL operations: select, filter, sort, join,
aggregate. Filters submit as a GET form so the result is bookmarkable and the
back button works, which is what lets Grace leave with one link.

The division of labour follows the project spec section 7. SQL filters, sorts, joins
and aggregates. Python validates the input before it reaches the database,
whitelists the sort column, and formats the output for reading. Nothing is
sorted or aggregated in Python.
"""

from flask import Blueprint, render_template, request

import db
import exports

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

# The region table is seven rows, so it gets a sort of its own but no pager.
# Its parameter is `rsort`, not `sort`: two controls sharing one name would put
# it twice in the query string, and only the first occurrence is ever read.
REGION_SORT_KEYS = {
    "coverage_desc": "avg_weighted IS NULL, avg_weighted DESC, region_name ASC",
    "coverage_asc":  "avg_weighted IS NULL, avg_weighted ASC,  region_name ASC",
    "countries":     "n_countries DESC, region_name ASC",
    "region":        "region_name ASC",
}
REGION_SORT_LABELS = [
    ("coverage_desc", "Coverage, highest first"),
    ("coverage_asc",  "Coverage, lowest first"),
    ("countries",     "Most countries first"),
    ("region",        "Region name"),
]
DEFAULT_REGION_SORT = "coverage_desc"

# A typo in the source data, corrected for display only. Never
# rewrite the supplied table.
REGION_DISPLAY_FIX = {"Latin America & Carribean": "Latin America & Caribbean"}


# Export columns, declared once and shared by CSV and PDF. Each formatter is
# the one the template uses, so the downloaded file and the screen agree, and
# each turns None into "no data" rather than an empty cell.
COLUMNS = [
    ("Country", "country_name", str),
    ("Region", "region_name", lambda v: fix_region(v) if v else db.BLANK),
    ("Coverage %", "coverage_reported", db.fmt_num),
    ("Gap to threshold pp", "gap_to_threshold", db.fmt_num),
    ("Target birth cohort", "target_cohort", db.fmt_int),
    ("Doses per 100 population", "doses_per_100_population", db.fmt_num),
    ("Herd immunity status", "herd_immunity_status", str),
]


def fix_region(name):
    return REGION_DISPLAY_FIX.get(name, name)


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
    submitted = ("submitted" in request.args
                 or request.args.get("format") in exports.FORMATS)
    if not submitted:
        return render_template(
            "pages/2a_coverage.html",
            db_missing=None, submitted=False,
            antigens=antigens, years=years, regions=regions, countries=countries,
            antigen=None, year=None, region=None, country=None,
            sort_active=DEFAULT_SORT, sort_labels=SORT_LABELS,
            rsort_active=DEFAULT_REGION_SORT, region_sort_labels=REGION_SORT_LABELS,
            summary=None, region_view=[], rows=[], threshold=None,
            conflict=None, rejected=[], fix_region=fix_region,
            page=db.paginate([], None), table_args={}, pdf_ok=False,
            fmt_int=db.fmt_int, fmt_big=db.fmt_big, fmt_pct=db.fmt_pct,
            fmt_num=db.fmt_num,
        )

    # An absent parameter falls back to the default; an invalid one falls back
    # to no filter. Those are different, and conflating them would silently
    # widen a selection the visitor thought was narrow.
    rejected = []

    if "antigen" in request.args:
        antigen, bad = db.validate(request.args.get("antigen"), valid_antigens)
        if bad:
            rejected.append("antigen")
    else:
        antigen = defaults["default_antigen"]

    if "year" in request.args:
        year, bad = db.validate(request.args.get("year"), valid_years, int)
        if bad:
            rejected.append("year")
    else:
        year = defaults["default_year"]

    region, bad = db.validate(request.args.get("region"), valid_regions, int)
    if bad:
        rejected.append("region")
    country, bad = db.validate(request.args.get("country"), valid_countries)
    if bad:
        rejected.append("country")

    sort = request.args.get("sort")
    order_by = db.safe_order_by(sort, SORT_KEYS, DEFAULT_SORT)
    sort_active = sort if sort in SORT_KEYS else DEFAULT_SORT
    if sort is not None and sort not in SORT_KEYS:
        rejected.append("sort order")

    rsort = request.args.get("rsort")
    region_order_by = db.safe_order_by(rsort, REGION_SORT_KEYS, DEFAULT_REGION_SORT)
    rsort_active = rsort if rsort in REGION_SORT_KEYS else DEFAULT_REGION_SORT
    if rsort is not None and rsort not in REGION_SORT_KEYS:
        rejected.append("region sort order")

    # Looked up BEFORE the queries run, because coverage_by_region binds it:
    # the regional table counts how many of a region's countries cleared this
    # bar. A threshold is a property of one disease, so there is none to apply
    # until a single antigen has been chosen.
    threshold = None
    if antigen:
        threshold = db.query_one(db.load_query("threshold_for_antigen"),
                                 {"antigen": antigen})

    params = {"antigen": antigen, "year": year,
              "region": region, "country": country,
              "threshold": threshold["threshold_pct"] if threshold else None}

    summary = db.query_one(db.load_query("coverage_selection_summary"), params)
    outcome = db.query_one(db.load_query("coverage_outcome"), params)
    # The region query is a UNION ALL, so its own ORDER BY has to sit outside
    # the compound select -- hence the subquery wrapper.
    region_rows = db.query(
        "SELECT * FROM (" + db.load_query("coverage_by_region") + ") ORDER BY "
        + region_order_by, params)
    # The only concatenation allowed near SQL in this project. order_by can only
    # be one of the literal strings in SORT_KEYS.
    rows = db.query(db.load_query("coverage_by_country") + " ORDER BY " + order_by,
                    params)

    # An export is the whole filtered, sorted result -- never the page on
    # screen. Placed before the remaining page queries so a download does not
    # pay for work it will not use.
    response = exports.send(
        request.args.get("format"),
        "coverage_%s_%s" % (antigen or "all", year or "all"),
        "Vaccination rates by country",
        "%s - %s" % (antigen or "all antigens", year or "all years"),
        COLUMNS, rows,
    )
    if response is not None:
        return response

    # Paginate the country table with a ?page= GET link so it works without
    # JavaScript and stays bookmarkable. The full `rows` is kept above, so an
    # export still contains every row.
    page = db.paginate(rows, request.args.get("page"), request.args.get("per_page"))
    if page["rejected"]:
        rejected.append("page or rows-per-page")

    # Every link and form on the page builds its URL from this dict, so the
    # pager, the two tables' controls and the export links cannot disagree.
    table_args = {
        "antigen": antigen, "year": year, "region": region, "country": country,
        "sort": sort_active, "per_page": page["size"], "rsort": rsort_active,
        "submitted": 1,
    }

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

    return render_template(
        "pages/2a_coverage.html",
        db_missing=None, submitted=True,
        antigens=antigens, years=years, regions=regions, countries=countries,
        antigen=antigen, year=year, region=region, country=country,
        sort_active=sort_active, sort_labels=SORT_LABELS,
        rsort_active=rsort_active, region_sort_labels=REGION_SORT_LABELS,
        summary=summary, outcome=outcome, region_view=region_view, rows=rows,
        page=page, table_args=table_args, pdf_ok=exports.pdf_available(),
        threshold=threshold, conflict=conflict, rejected=rejected,
        fix_region=fix_region,
        fmt_int=db.fmt_int, fmt_big=db.fmt_big, fmt_pct=db.fmt_pct,
        fmt_num=db.fmt_num,
    )
