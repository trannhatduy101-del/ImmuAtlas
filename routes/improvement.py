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

from flask import Blueprint, render_template, request

import db
import exports

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

# Export columns, declared once and shared by CSV and PDF. Each formatter is
# the one the template uses, so the file and the screen agree, and each turns
# None into "no data" rather than an empty cell.
COLUMNS = [
    ("Rank", "improvement_rank", db.fmt_int),
    ("Country", "country_name", str),
    ("Region", "region_name", str),
    ("Coverage start %", "coverage_start", db.fmt_num),
    ("Coverage end %", "coverage_end", db.fmt_num),
    ("Change pp", "coverage_change", db.fmt_num),
    ("Cases per 100k start", "cases_start", db.fmt_num),
    ("Cases per 100k end", "cases_end", db.fmt_num),
    ("Case change", "case_change", db.fmt_num),
    # Population denominator. Four decimals because doses per 100 of a whole
    # national population is a small number -- rounded to two it reads 0.00 for
    # most countries and the column looks empty rather than small.
    ("Doses per 100 pop start", "doses_per_100_start", lambda v: db.fmt_num(v, 4)),
    ("Doses per 100 pop end", "doses_per_100_end", lambda v: db.fmt_num(v, 4)),
    ("Doses per 100 pop change", "doses_per_100_change", lambda v: db.fmt_num(v, 4)),
]


def _rows_for(antigen, start_year, end_year, order_by):
    """Run the ranked improvement query. `order_by` is a trusted SORT_KEYS
    fragment; every value the user supplied is a bound parameter.

    Returns the WHOLE eligible pool, not a top-N slice. The "Countries" control
    is now a page size, so the reader can walk past rank 10 and an export can
    contain every ranked country instead of only the first page.
    """
    # Wrap the join in a subquery so ORDER BY resolves against the SELECT's
    # output aliases (country_name etc. exist in several joined views, so an
    # unwrapped ORDER BY on them is ambiguous). order_by is a trusted fragment.
    base = db.load_query("coverage_improvement")
    sql = "SELECT * FROM (" + base + ") ORDER BY " + order_by
    params = {"antigen": antigen, "start_year": start_year,
              "end_year": end_year}
    return db.query(sql, params)


def _summary_for(antigen, start_year, end_year):
    """Headline figures for the KPI row, aggregated in SQL over the eligible
    pool (never in Python): average and largest coverage gain, and how many
    countries also saw their reported case rate fall."""
    base = db.load_query("coverage_improvement")
    sql = ("SELECT ROUND(AVG(coverage_change), 1) AS avg_gain, "
           "ROUND(MAX(coverage_change), 1)        AS max_gain, "
           "SUM(CASE WHEN case_change < 0 THEN 1 ELSE 0 END)          AS n_cases_fell, "
           "SUM(CASE WHEN case_change IS NOT NULL THEN 1 ELSE 0 END)  AS n_with_cases "
           "FROM (" + base + ")")
    return db.query_one(sql, {"antigen": antigen, "start_year": start_year,
                              "end_year": end_year})


def _gain_bars(rows):
    """Diverging vertical-bar geometry (VaxVision-style dashboard):
    one column per country, growing up from a zero line for a gain and down for
    a decline. Each side of the zero line is scaled independently against the
    largest change on that side, so the biggest gain and the biggest decline
    both reach the edge of the plot. This is display formatting (a number to a
    percentage), so it belongs here, not in SQL or the template.
    """
    changes = [r["coverage_change"] for r in rows if r["coverage_change"] is not None]
    max_gain = max([0.0] + [c for c in changes if c > 0])
    max_loss = max([0.0] + [-c for c in changes if c < 0])
    span = max_gain + max_loss
    # The zero line sits proportionally to which side needs more room, kept
    # within [15, 85] so a bar is never squashed flat when one side dominates
    # -- but only when both sides actually have a bar; a side with none gets
    # no reserved space (else an all-gain ranking wastes most of the plot).
    if not span:
        zero_pct = 50.0
    elif max_loss == 0:
        zero_pct = 100.0
    elif max_gain == 0:
        zero_pct = 0.0
    else:
        zero_pct = round(max(15.0, min(85.0, max_loss / span * 100)), 2)

    bars = []
    for r in rows:
        change = r["coverage_change"]
        if change is None:
            bars.append({"row": r, "up": True, "top_pct": zero_pct, "height_pct": 0.0})
            continue
        up = change >= 0
        if up:
            height_pct = round(change / max_gain * zero_pct, 2) if max_gain else 0.0
            top_pct = round(zero_pct - height_pct, 2)
        else:
            height_pct = round(-change / max_loss * (100 - zero_pct), 2) if max_loss else 0.0
            top_pct = zero_pct
        bars.append({"row": r, "up": up, "top_pct": top_pct,
                     "height_pct": height_pct,
                     # Rank comes from SQL and is always by gain, so the single
                     # biggest improver stays marked whatever the table sort is.
                     "is_top": r["improvement_rank"] == 1})
    return {"zero_pct": zero_pct, "bars": bars}


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
    submitted = ("submitted" in request.args
                 or request.args.get("format") in exports.FORMATS)
    disease_for = {a["antigen"]: a["disease_name"] for a in antigens}
    name_for = {a["antigen"]: a["antigen_name"] for a in antigens}

    rejected = []

    # Antigen and the two years are REQUIRED: the page leaves them unset so the
    # visitor chooses them (the form marks them with a red * and HTML `required`).
    # No silent default is filled in, so a ranking never appears for a period the
    # visitor did not actually pick.
    antigen, bad = db.validate(request.args.get("antigen"), valid_antigens)
    if bad:
        rejected.append("antigen")

    start_year, bad = db.validate(request.args.get("start"), valid_years, int)
    if bad:
        rejected.append("start year")

    end_year, bad = db.validate(request.args.get("end"), valid_years, int)
    if bad:
        rejected.append("end year")

    count, bad = db.validate(request.args.get("n"), set(COUNT_OPTIONS), int)
    if bad:
        rejected.append("number of countries")
    if count is None:
        count = DEFAULT_COUNT

    sort = request.args.get("sort")
    order_by = db.safe_order_by(sort, SORT_KEYS, DEFAULT_SORT)
    sort_active = sort if sort in SORT_KEYS else DEFAULT_SORT
    if sort is not None and sort not in SORT_KEYS:
        rejected.append("sort order")

    # The End year dropdown only offers years after the chosen start, so the
    # invalid half of the range is not on the menu at all. Narrowing happens on
    # the next render because the site carries no JavaScript -- the page says
    # so under the field rather than leaving the reader to wonder.
    #
    # Only the END list is narrowed. Filtering the start list by the chosen end
    # would trap a reader who picked 2010-2015 and then wants to reach further
    # back: 2005 would no longer be offered as a start.
    end_years = ([y for y in years if y["year"] > start_year]
                 if start_year is not None else list(years))

    # This stays the real guard. A hand-typed ?start=2015&end=2000 never touches
    # the dropdown, so the check cannot live in the markup.
    # The end year must be after the start year, or "improvement over a period"
    # has no meaning. Say so rather than returning a confusing empty table.
    range_error = (start_year is not None and end_year is not None
                   and end_year <= start_year)

    # Every link and form on the page builds its URL from this dict, so the
    # pager, the table controls and the export links cannot disagree about the
    # current selection. It holds validated values only -- never request.args,
    # which would round-trip a value the page just reported as rejected.
    table_args = {
        "antigen": antigen, "start": start_year, "end": end_year,
        "n": count, "sort": sort_active, "submitted": 1,
    }

    ctx = dict(
        db_missing=None,
        antigens=antigens, years=years, end_years=end_years,
        antigen=antigen, antigen_name=name_for.get(antigen),
        disease_name=disease_for.get(antigen),
        start_year=start_year, end_year=end_year,
        count=count, count_options=COUNT_OPTIONS,
        sort_active=sort_active, sort_labels=SORT_LABELS,
        rejected=rejected, range_error=range_error, submitted=submitted,
        rows=[], bars={"zero_pct": 50.0, "bars": []}, eligible=0,
        imp_summary=None, top_gainer=None,
        page=db.paginate([], None), table_args=table_args,
        pdf_ok=exports.pdf_available(),
        fmt_int=db.fmt_int, fmt_pct=db.fmt_pct, fmt_num=db.fmt_num,
    )

    # A required field left unchosen means the visitor hasn't really submitted a
    # selection yet -> show the "pick your fields" prompt rather than an empty
    # result that looks like a data gap.
    missing_required = antigen is None or start_year is None or end_year is None
    if not submitted or missing_required:
        ctx["submitted"] = False
        return render_template("pages/3a_improvement.html", **ctx)
    if range_error:
        return render_template("pages/3a_improvement.html", **ctx)

    # The whole eligible pool, ordered by the reader's chosen sort.
    rows = _rows_for(antigen, start_year, end_year, order_by)
    ctx["rows"] = rows

    # An export is the full pool, never the page on screen -- the old version
    # could only ever hand over the top N.
    response = exports.send(
        request.args.get("format"),
        "improvement_%s_%s-%s" % (antigen, start_year, end_year),
        "Biggest improvement in coverage",
        "%s - %s to %s" % (name_for.get(antigen, antigen), start_year, end_year),
        COLUMNS, rows,
    )
    if response is not None:
        return response

    # The pool size IS the row count, so the separate COUNT(*) round trip the
    # old _eligible_count() did is gone.
    page = db.paginate(rows, request.args.get("page"), count,
                       sizes=COUNT_OPTIONS, default_size=DEFAULT_COUNT)
    if page["rejected"]:
        rejected.append("page")
    ctx["page"] = page
    ctx["eligible"] = page["total"]
    ctx["imp_summary"] = _summary_for(antigen, start_year, end_year)

    # The single biggest gainer, for the KPI row, regardless of the table sort.
    # It is rank 1 by construction, so it is already in `rows`.
    ctx["top_gainer"] = next((r for r in rows if r["improvement_rank"] == 1), None)

    # The chart draws the page the reader is looking at, so chart and table
    # always show the same countries.
    ctx["bars"] = _gain_bars(page["rows"])

    return render_template("pages/3a_improvement.html", **ctx)
