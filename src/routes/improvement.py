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
import worldmap

bp = Blueprint("improvement", __name__)


# A user-chosen sort cannot be a bound parameter, so each option is written out
# here and the request can only pick one of these keys. Every key ends on
# country_name so ties resolve deterministically, and pushes NULLs last in both
# directions so "no data" never leads the ranking.
SORT_KEYS = {
    "gain_desc":  "coverage_change IS NULL, coverage_change DESC, country_name ASC",
    "gain_asc":   "coverage_change IS NULL, coverage_change ASC,  country_name ASC",
    "end_desc":   "coverage_end IS NULL, coverage_end DESC,       country_name ASC",
    "end_asc":    "coverage_end IS NULL, coverage_end ASC,        country_name ASC",
    # The start year was only ever a number on screen, never something you could
    # order by -- so "who began furthest behind" could not be asked.
    "start_asc":  "coverage_start IS NULL, coverage_start ASC,    country_name ASC",
    "cases_fell": "case_change IS NULL, case_change ASC,          country_name ASC",
    "cases_rose": "case_change IS NULL, case_change DESC,         country_name ASC",
    # Sorts on the case rate the table actually SHOWS at the end year. Every
    # other case key orders by the change, which answers a different question.
    "cases_now":  "cases_end IS NULL, cases_end DESC,             country_name ASC",
    "pop_rate":   ("doses_per_100_change IS NULL, doses_per_100_change DESC, "
                   "country_name ASC"),
    "pop_rate_asc": ("doses_per_100_change IS NULL, doses_per_100_change ASC, "
                     "country_name ASC"),
    "country":    "country_name ASC",
    "country_desc": "country_name DESC",
}
# Same shape as the 2A labels: "what is being sorted: which direction", and no
# "first". The three case options are worded so they cannot be confused: the two
# "Change in case rate" ones order by how far the rate MOVED, while "Case rate
# in the end year" orders by the rate the table actually shows.
SORT_LABELS = [
    ("gain_desc",  "Gain: high → low"),
    ("gain_asc",   "Gain: low → high"),
    ("end_desc",   "End coverage: high → low"),
    ("end_asc",    "End coverage: low → high"),
    ("start_asc",  "Start coverage: low → high"),
    ("cases_fell", "Case change: biggest fall"),
    ("cases_rose", "Case change: biggest rise"),
    ("cases_now",  "End case rate: high → low"),
    ("pop_rate",   "Doses/100: high → low"),
    ("pop_rate_asc", "Doses/100: low → high"),
    ("country",    "Country: A – Z"),
    ("country_desc", "Country: Z – A"),
]
DEFAULT_SORT = "gain_desc"

# How many countries to rank. A fixed set, so the value is a whitelist check
# rather than an unbounded number spliced anywhere near the SQL.
COUNT_OPTIONS = (5, 10, 20, 50)
DEFAULT_COUNT = 10

# How many columns the bar chart draws. Fixed, and deliberately NOT the page
# size: the chart answers "who improved most", which does not change when the
# reader re-sorts the table or walks to page 3.
CHART_BARS = 10

# Export columns, declared once and shared by CSV and PDF. Each formatter is
# the one the template uses, so the file and the screen agree, and each turns
# None into "no data" rather than an empty cell.
COLUMNS = [
    ("Rank", "improvement_rank", db.fmt_int),
    ("Country", "country_name", str),
    ("Region", "region_name", str),
    ("Coverage start %", "coverage_start", db.fmt_num),
    ("Coverage end %", "coverage_end", db.fmt_num),
    ("Change (percentage points)", "coverage_change", db.fmt_num),
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


def _rows_for(antigen, start_year, end_year, order_by, below_only=None, q=None):
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
              "end_year": end_year, "below_only": below_only, "q": q}
    return db.query(sql, params)


def _summary_for(antigen, start_year, end_year, below_only=None, q=None):
    """Headline figures for the KPI row, aggregated in SQL over the eligible
    pool (never in Python): average and largest coverage gain, and how many
    countries also saw their reported case rate fall."""
    base = db.load_query("coverage_improvement")
    sql = ("SELECT ROUND(AVG(coverage_change), 1) AS avg_gain, "
           "ROUND(MAX(coverage_change), 1)        AS max_gain, "
           "SUM(CASE WHEN case_change < 0 THEN 1 ELSE 0 END)          AS n_cases_fell, "
           "SUM(CASE WHEN case_change IS NOT NULL THEN 1 ELSE 0 END)  AS n_with_cases "
           "FROM (" + base + ")")
    # Same below_only as the table: a headline computed over a different pool
    # from the rows underneath it is worse than no headline.
    return db.query_one(sql, {"antigen": antigen, "start_year": start_year,
                              "end_year": end_year, "below_only": below_only,
                              "q": q})


def _gain_bars(rows):
    """Diverging vertical-bar geometry:
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


# The globe's colour scale. Coverage at the end year, in the same language the
# rest of the site uses: orange under the target, blue at or above it, two steps
# of each so a country that just cleared the bar does not look like one at 100%.
# Grey is "no figure", never a shade of the scale -- a country with nothing to
# report must not read as a low number.
GLOBE_NO_DATA = "#d3e2ee"
GLOBE_SCALE = [
    (70.0,  "#9a3412"),   # far below
    (90.0,  "#e06024"),   # below the target
    (95.0,  "#3b8fc4"),   # just over
    (None,  "#075985"),   # comfortably over
]
GLOBE_TARGET = 90.0


def globe_paths(rows):
    """One drawable shape per country, coloured by its end-year coverage.

    Reads the rows the ranking table already has, so the globe costs no extra
    query. A country the ranking excluded -- no figure in both years -- keeps
    its outline but takes the no-data grey, because leaving it off the map
    entirely would punch a hole in the world.
    """
    coverage = {r["country_id"]: r["coverage_end"] for r in rows}
    shapes = []
    for iso in sorted(worldmap.PATHS):
        value = coverage.get(iso)
        fill = GLOBE_NO_DATA
        if value is not None:
            for limit, colour in GLOBE_SCALE:
                if limit is None or value < limit:
                    fill = colour
                    break
        shapes.append({"iso": iso, "d": worldmap.PATHS[iso],
                       "fill": fill, "value": value})
    return shapes


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

    # A single opt-in value. Anything else is rejected rather than coerced, so
    # a hand-typed ?below_only=maybe cannot quietly narrow someone's ranking.
    below_only, bad = db.validate(request.args.get("below_only"), {"1"})
    if bad:
        rejected.append("below-threshold filter")

    # Search text: free by nature, so trimmed and capped rather than checked
    # against a whitelist, and bound into the SQL so % and _ are characters to
    # look for rather than a pattern the reader gets to write.
    query_text = (request.args.get("q") or "").strip()[:60] or None

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
        "below_only": below_only, "q": query_text,
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
        below_only=below_only, query_text=query_text,
        rows=[], bars={"zero_pct": 50.0, "bars": []}, eligible=0, chart_n=0,
        globe=[], globe_w=worldmap.WIDTH, globe_h=worldmap.HEIGHT,
        globe_credit=worldmap.CREDIT, globe_target=GLOBE_TARGET,
        imp_summary=None, top_gainer=None,
        tied_ranks=set(),
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
    rows = _rows_for(antigen, start_year, end_year, order_by, below_only,
                     query_text)
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
    # Which ranks more than one country shares. RANK() repeats a number on a
    # tie, and an unexplained repeated "12" reads as a bug rather than as two
    # countries that gained exactly the same.
    tally = {}
    for r in rows:
        tally[r["improvement_rank"]] = tally.get(r["improvement_rank"], 0) + 1
    ctx["tied_ranks"] = {rank for rank, n in tally.items() if n > 1}

    ctx["page"] = page
    ctx["eligible"] = page["total"]
    ctx["imp_summary"] = _summary_for(antigen, start_year, end_year, below_only,
                                      query_text)

    # The single biggest gainer, for the KPI row, regardless of the table sort.
    # It is rank 1 by construction, so it is already in `rows`.
    ctx["top_gainer"] = next((r for r in rows if r["improvement_rank"] == 1), None)

    # The chart is ALWAYS the ten biggest improvers, whatever the table is
    # sorted by and whatever page the reader is on. Drawing the current page
    # meant "sort by country name" produced a chart of ten countries beginning
    # with A -- a ranked bar chart of nothing in particular. Ordered by SQL
    # (gain_desc) and sliced here; Python never sorts. Same below_only as the
    # table, so the chart and the rows beneath it describe the same pool.
    # Deliberately unsearched: the chart is the ten biggest improvers of the
    # ranking, and a search box narrowing the table should not silently redraw
    # what "the top ten" means.
    top_rows = _rows_for(antigen, start_year, end_year,
                         SORT_KEYS["gain_desc"], below_only)[:CHART_BARS]
    ctx["bars"] = _gain_bars(top_rows)
    ctx["globe"] = globe_paths(rows)
    ctx["chart_n"] = len(top_rows)

    return render_template("pages/3a_improvement.html", **ctx)
