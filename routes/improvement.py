"""3A Biggest improvement in coverage -- Sub-Task A.

The Level-3 deep dive: rank countries by how much their reported coverage rose
for one antigen between a start and an end year, then join that against the
change in reported case rate over the same period so the page can answer whether
disease burden ACTUALLY fell -- not just whether effort went up.

Division of labour follows the project spec section 7. SQL does the self-join, the
subtraction, the filtering and the ranking (coverage_improvement.sql). Python
validates every input before it reaches the database, whitelists the sort
column, turns the numbers into bar geometry, and formats the output. Nothing is
sorted or aggregated in Python.
"""

import csv
import io

from flask import Blueprint, render_template, request, Response

import db

bp = Blueprint("improvement", __name__)


# A user-chosen sort cannot be a bound parameter, so each option is written out
# here and the request can only pick one of these keys. Every key ends on
# country_name so ties resolve deterministically, and pushes NULLs last in both
# directions so "no data" never leads the ranking.
SORT_KEYS = {
    "gain_desc":  "coverage_change IS NULL, coverage_change DESC, country_name ASC",
    "gain_asc":   "coverage_change IS NULL, coverage_change ASC,  country_name ASC",
    "end_desc":   "coverage_end IS NULL, coverage_end DESC,       country_name ASC",
    "cases_fell": "case_change IS NULL, case_change ASC,          country_name ASC",
    "country":    "country_name ASC",
}
SORT_LABELS = [
    ("gain_desc",  "Biggest coverage gain first"),
    ("gain_asc",   "Smallest gain (or decline) first"),
    ("end_desc",   "Highest end coverage first"),
    ("cases_fell", "Largest fall in case rate first"),
    ("country",    "Country name"),
]
DEFAULT_SORT = "gain_desc"

# How many countries to rank. A fixed set, so the value is a whitelist check
# rather than an unbounded number spliced anywhere near the SQL.
COUNT_OPTIONS = (5, 10, 20, 50)
DEFAULT_COUNT = 10


def _validate(raw, allowed, cast=str):
    """Resolve a request value against the set we actually offer.

    Returns (value, rejected). A value not on the list never reaches the
    database, and the fact that it was dropped is returned so the page can say
    so rather than silently widening the selection.
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


def _rows_for(antigen, start_year, end_year, order_by, limit):
    """Run the ranked improvement query. `order_by` is a trusted SORT_KEYS
    fragment; every value the user supplied is a bound parameter."""
    # Wrap the join in a subquery so ORDER BY resolves against the SELECT's
    # output aliases (country_name etc. exist in several joined views, so an
    # unwrapped ORDER BY on them is ambiguous). order_by is a trusted fragment.
    base = db.load_query("coverage_improvement")
    sql = "SELECT * FROM (" + base + ") ORDER BY " + order_by + " LIMIT :limit"
    params = {"antigen": antigen, "start_year": start_year,
              "end_year": end_year, "limit": limit}
    return db.query(sql, params)


def _eligible_count(antigen, start_year, end_year):
    """How many countries reported this antigen in BOTH years -- the pool the
    top-N is drawn from, for an honest 'N of M' summary."""
    base = db.load_query("coverage_improvement")
    sql = "SELECT COUNT(*) FROM (" + base + ")"
    return db.scalar(sql, {"antigen": antigen, "start_year": start_year,
                           "end_year": end_year}) or 0


def _dumbbell(rows, axis_max):
    """Turn each row into bar geometry for the dumbbell chart. Percentages of
    axis_max; direction so a decline can be drawn differently from a gain. This
    is display formatting (a number to a width), so it belongs here, not in SQL.
    """
    view = []
    for r in rows:
        start = r["coverage_start"]
        end = r["coverage_end"]
        p_start = max(0.0, min(100.0, start / axis_max * 100)) if start is not None else 0.0
        p_end = max(0.0, min(100.0, end / axis_max * 100)) if end is not None else 0.0
        up = (end or 0) >= (start or 0)
        view.append({
            "row": r,
            "p_start": round(p_start, 2),
            "p_end": round(p_end, 2),
            "bar_left": round(min(p_start, p_end), 2),
            "bar_width": round(abs(p_end - p_start), 2),
            "up": up,
        })
    return view


@bp.route("/improvement")
def index():
    try:
        antigens = db.query(db.load_query("filter_antigens"))
        years = db.query(db.load_query("filter_years"))
    except db.DatabaseMissing as exc:
        return render_template("pages/3a_improvement.html", db_missing=str(exc)), 503

    valid_antigens = {a["antigen"] for a in antigens}
    valid_years = {y["year"] for y in years}

    # The dropdowns land pre-filled with a sensible default period, but nothing
    # is ranked until the visitor presses Rank (the form carries submitted=1).
    # A CSV request always implies a submitted selection.
    submitted = "submitted" in request.args or request.args.get("format") == "csv"
    year_values = sorted(valid_years)
    disease_for = {a["antigen"]: a["disease_name"] for a in antigens}
    name_for = {a["antigen"]: a["antigen_name"] for a in antigens}

    rejected = []

    # Antigen: default to the first offered so the page always lands on data.
    antigen, bad = _validate(request.args.get("antigen"), valid_antigens)
    if bad:
        rejected.append("antigen")
    if antigen is None:
        antigen = antigens[0]["antigen"] if antigens else None

    # Years: default to the full span, which is where improvement is largest and
    # matches the brief's own example (2000 to 2024).
    start_year, bad = _validate(request.args.get("start"), valid_years, int)
    if bad:
        rejected.append("start year")
    if start_year is None:
        start_year = year_values[0] if year_values else None

    end_year, bad = _validate(request.args.get("end"), valid_years, int)
    if bad:
        rejected.append("end year")
    if end_year is None:
        end_year = year_values[-1] if year_values else None

    count, bad = _validate(request.args.get("n"), set(COUNT_OPTIONS), int)
    if bad:
        rejected.append("number of countries")
    if count is None:
        count = DEFAULT_COUNT

    sort = request.args.get("sort")
    order_by = db.safe_order_by(sort, SORT_KEYS, DEFAULT_SORT)
    sort_active = sort if sort in SORT_KEYS else DEFAULT_SORT
    if sort is not None and sort not in SORT_KEYS:
        rejected.append("sort order")

    # The end year must be after the start year, or "improvement over a period"
    # has no meaning. Say so rather than returning a confusing empty table.
    range_error = (start_year is not None and end_year is not None
                   and end_year <= start_year)

    ctx = dict(
        db_missing=None,
        antigens=antigens, years=years,
        antigen=antigen, antigen_name=name_for.get(antigen),
        disease_name=disease_for.get(antigen),
        start_year=start_year, end_year=end_year,
        count=count, count_options=COUNT_OPTIONS,
        sort_active=sort_active, sort_labels=SORT_LABELS,
        rejected=rejected, range_error=range_error, submitted=submitted,
        rows=[], view=[], eligible=0, axis_max=100,
        fmt_int=db.fmt_int, fmt_pct=db.fmt_pct,
    )

    if not submitted or range_error or antigen is None:
        return render_template("pages/3a_improvement.html", **ctx)

    rows = _rows_for(antigen, start_year, end_year, order_by, count)
    ctx["rows"] = rows
    ctx["eligible"] = _eligible_count(antigen, start_year, end_year)

    # CSV export of exactly what is shown: same antigen, years, N and sort.
    if request.args.get("format") == "csv":
        return _csv_response(rows, antigen, start_year, end_year)

    # Axis runs 0 to at least 100; extend it when coverage above 100% is kept
    # (doses outside the target cohort are real and never capped, the project spec 4.5).
    ceiling = max([100] + [r["coverage_end"] for r in rows
                           if r["coverage_end"] is not None]
                          + [r["coverage_start"] for r in rows
                             if r["coverage_start"] is not None])
    axis_max = int((ceiling + 9) // 10 * 10)
    ctx["axis_max"] = axis_max
    ctx["view"] = _dumbbell(rows, axis_max)

    return render_template("pages/3a_improvement.html", **ctx)


def _csv_response(rows, antigen, start_year, end_year):
    """Stream the ranked result as CSV. Same figures as the table, so a reader
    can take the numbers away and check them."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["country", "region",
                "coverage_%s" % start_year, "coverage_%s" % end_year,
                "coverage_change_pp",
                "cases_per_100k_%s" % start_year, "cases_per_100k_%s" % end_year,
                "case_rate_change"])
    for r in rows:
        w.writerow([r["country_name"], r["region_name"],
                    r["coverage_start"], r["coverage_end"], r["coverage_change"],
                    r["cases_start"], r["cases_end"], r["case_change"]])
    fname = "improvement_%s_%s-%s.csv" % (antigen, start_year, end_year)
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=%s" % fname})
