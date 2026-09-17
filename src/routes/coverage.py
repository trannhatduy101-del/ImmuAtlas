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
#
# Every key here orders a column the table actually shows. Sorting by something
# off screen produces an order the reader cannot account for, so it reads as no
# order at all: that is why target_cohort left, and why gap_to_threshold left
# too -- it was coverage minus a constant, a second name for a sort already in
# the list.
SORT_KEYS = {
    # coverage_display, not coverage_reported: the table prints the capped
    # figure, so ordering on the raw one would put 169.3% above 154.8% while
    # both cells read "100.0%" -- a control announcing an order the table is
    # not in, which is the exact bug this page has already had once.
    "coverage_desc": "coverage_display IS NULL, coverage_display DESC, country_name ASC",
    "coverage_asc":  "coverage_display IS NULL, coverage_display ASC,  country_name ASC",
    "country":       "country_name ASC",
    "country_desc":  "country_name DESC",
    "region":        "region_name ASC, country_name ASC",
    "region_desc":   "region_name DESC, country_name ASC",
    # Antigen and Year became columns on this table, so they became things a
    # reader can expect to order by.
    "antigen":       "antigen ASC,  year DESC, country_name ASC",
    "antigen_desc":  "antigen DESC, year DESC, country_name ASC",
    "year_desc":     "year DESC, country_name ASC",
    "year_asc":      "year ASC,  country_name ASC",
}
# One shape for every option: "what is being sorted: which direction". It reads
# the same way in the dropdown and inside the "sorted by ..." sentence under the
# table, which lowercases whatever is chosen. No "first" -- ordering is what a
# sort control does, so the word carried no information.
SORT_LABELS = [
    ("coverage_desc", "% of target: high → low"),
    ("coverage_asc",  "% of target: low → high"),
    ("country",       "Country: A – Z"),
    ("country_desc",  "Country: Z – A"),
    ("antigen",       "Antigen: A – Z"),
    ("antigen_desc",  "Antigen: Z – A"),
    ("year_desc",     "Year: new → old"),
    ("year_asc",      "Year: old → new"),
    ("region",        "Region: A – Z"),
    ("region_desc",   "Region: Z – A"),
]
# Alphabetical, not "% of target: high to low". Every row here already cleared
# the 90% bar, and 15% of them sit at 100 -- so the descending sort opened on two
# full pages of "100.0%" and the table read as though every country were at the
# ceiling. A-Z opens on the actual spread (90.4, 94.0, 95.0, 98.9, 100.0); the
# coverage sorts are still one click away.
DEFAULT_SORT = "country"

# 2A measures every antigen against one 90% bar, the benchmark the brief names:
# "all countries that have met at least 90% of their vaccination targets".
# WHO's own targets differ by disease -- 95% measles, 90% DTP, 80% rubella --
# and they stay in herd_immunity_threshold, are still read for the method note,
# and are still what 3A filters on. This page simply does not rank against them.
BRIEF_THRESHOLD = 90.0

# The region table has its own sort, and the same rule applies: only columns on
# screen. Average coverage, countries in selection and countries reporting were
# offered here until they stopped being columns; they stay in the download.
# Its parameter is `rsort`, not `sort`: two controls sharing one name would put
# it twice in the query string, and only the first occurrence is ever read.
REGION_SORT_KEYS = {
    "met":           "n_met_threshold DESC, region_name ASC",
    "met_asc":       "n_met_threshold ASC,  region_name ASC",
    "region":        "region_name ASC, antigen ASC, year DESC",
    "region_desc":   "region_name DESC, antigen ASC, year DESC",
    # The table splits by antigen and year, so both are columns a reader sees
    # and therefore both are things they can order by.
    "antigen":       "antigen ASC,  region_name ASC, year DESC",
    "antigen_desc":  "antigen DESC, region_name ASC, year DESC",
    "year_desc":     "year DESC, region_name ASC",
    "year_asc":      "year ASC,  region_name ASC",
}
# Every key in REGION_SORT_KEYS appears here, and nothing else does. Offering a
# key without a label is what broke this control once: the default was a key
# filtered out of the labels, so no <option> matched, the browser showed the
# first one, and the page announced an order the table was not in.
REGION_SORT_LABELS = [
    ("met",           "Met target: high → low"),
    ("met_asc",       "Met target: low → high"),
    ("region",        "Region: A – Z"),
    ("region_desc",   "Region: Z – A"),
    ("antigen",       "Antigen: A – Z"),
    ("antigen_desc",  "Antigen: Z – A"),
    ("year_desc",     "Year: new → old"),
    ("year_asc",      "Year: old → new"),
]
# Most countries meeting the target first, which is the only figure this table
# actually shows. It used to default to "coverage_asc", a key that is not in the
# label list -- so no <option> matched, the browser displayed the first one, and
# the control announced an order the table was not in.
DEFAULT_REGION_SORT = "met"

# A typo in the source data, corrected for display only. Never
# rewrite the supplied table.
REGION_DISPLAY_FIX = {"Latin America & Carribean": "Latin America & Caribbean"}


# Export columns, declared once and shared by CSV and PDF. Each formatter is
# the one the template uses, so the downloaded file and the screen agree, and
# each turns None into "no data" rather than an empty cell.
COLUMNS = [
    ("Country", "country_name", str),
    # Antigen and Year are columns on screen (brief 2A, Table 1), so they are
    # columns in the download too -- a file of percentages with no antigen
    # beside them cannot be read once it leaves the page that produced it.
    ("Antigen", "antigen_name", str),
    # str, not fmt_int: a year is a label, and fmt_int writes it "2,011".
    ("Year", "year", str),
    ("Region", "region_name", lambda v: fix_region(v) if v else db.BLANK),
    # The figure on screen, capped at 100 like the brief's example, and then
    # the same figure as the country actually reported it. Both, because a file
    # that only carried the capped number would have quietly lost 1,312 real
    # measurements, and one that only carried the raw number would not match
    # the page it came from.
    ("Percentage of target %", "coverage_display", db.fmt_num),
    ("Reported % (uncapped)", "coverage_reported", db.fmt_num),
    ("Target birth cohort", "target_cohort", db.fmt_int),
    ("Doses per 100 population", "doses_per_100_population", db.fmt_num),
]


# The region table's download. It carries the columns the on-screen table
# dropped when it was cut to the brief's four -- average coverage, how many
# countries reported -- because a file is read away from the page that produced
# it and cannot rely on a chart standing beside it.
REGION_COLUMNS = [
    ("Region", "region_name", lambda v: fix_region(v) if v else db.BLANK),
    # The rows are one region per vaccine per year, so the file has to say which
    # vaccine and which year or 976 region names mean nothing.
    ("Antigen", "antigen", str),
    ("Year", "year", str),
    ("Countries that met the target", "n_met_threshold", db.fmt_int),
    ("Countries in selection", "n_countries", db.fmt_int),
    ("Countries reporting", "n_reporting", db.fmt_int),
    ("Average coverage % (weighted)", "avg_weighted", db.fmt_num),
    ("Average coverage % (unweighted)", "avg_unweighted", db.fmt_num),
]

# Which table a download is asking for. Two tables on one page means the URL has
# to say; anything else falls back to the country table, the one the page leads
# with.
EXPORT_TABLES = {"region", "country"}


# Long enough for the longest country name in the data, short enough that a
# pasted essay cannot become the filter.
SEARCH_MAX = 60


def search_text(raw):
    """A search box's value, or None when it is empty."""
    text = (raw or "").strip()[:SEARCH_MAX]
    return text or None


def fix_region(name):
    return REGION_DISPLAY_FIX.get(name, name)


@bp.route("/coverage")
def index():
    try:
        antigens = db.query(db.load_query("filter_antigens"))
        years = db.query(db.load_query("filter_years"))
        regions = db.query(db.load_query("filter_regions"))
        countries = db.query(db.load_query("filter_countries"))
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
            threshold_pct=BRIEF_THRESHOLD,
            query_text=None, region_query_text=None,
            summary=None, region_view=[], chart_view=[], rows=[], threshold=None,
            disease_of={},
            conflict=None, rejected=[], fix_region=fix_region,
            page=db.paginate([], None), rpage=db.paginate([], None),
            table_args={}, pdf_ok=False,
            fmt_int=db.fmt_int, fmt_big=db.fmt_big, fmt_pct=db.fmt_pct,
            fmt_num=db.fmt_num,
        )

    # Absent and empty both mean "no filter". They used to differ -- an absent
    # antigen fell back to a default one -- and that quietly changed the result
    # under the reader: neither url_for() nor hidden_args() can express "present
    # but empty", so choosing All antigens dropped the parameter from every link
    # on the page, and the next click came back as the default vaccine. The two
    # states are indistinguishable in a URL, so they have to mean the same
    # thing. An invalid value is still different, and still reported.
    rejected = []

    antigen, bad = db.validate(request.args.get("antigen"), valid_antigens)
    if bad:
        rejected.append("antigen")

    year, bad = db.validate(request.args.get("year"), valid_years, int)
    if bad:
        rejected.append("year")

    # RegionID is a code like "TEA", not a number. Casting to int here
    # threw on every real value, so the filter reported itself ignored and
    # the selection silently stayed wide.
    region, bad = db.validate(request.args.get("region"), valid_regions)
    if bad:
        rejected.append("region")
    country, bad = db.validate(request.args.get("country"), valid_countries)
    if bad:
        rejected.append("country")

    export_table, bad = db.validate(request.args.get("table"), EXPORT_TABLES)
    if bad:
        rejected.append("download table")

    # Search text. Not checked against a whitelist -- it is free text by nature
    # -- but trimmed, capped, and passed to SQL as a bound value, so % and _ are
    # characters to look for rather than a pattern the reader gets to write.
    query_text = search_text(request.args.get("q"))
    region_query_text = search_text(request.args.get("rq"))

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

    params = {"antigen": antigen, "year": year,
              "region": region, "country": country,
              # One bar for every antigen, under one name, so the regional
              # counts, the outcome verdict and the country filter all measure
              # the same thing.
              "met_threshold": BRIEF_THRESHOLD,
              # One row per region per antigen per year. Rolled up across the
              # whole dataset, "countries that met the target" counts a country
              # that managed it in any single year, and every region reads close
              # to 100%. 1A passes None and keeps the rolled-up shape.
              "detail": 1,
              # Each table searches its own column, so the two boxes never
              # narrow each other.
              "q": query_text}

    # The region query is a UNION ALL, so its own ORDER BY has to sit outside
    # the compound select -- hence the subquery wrapper.
    region_sql = ("SELECT * FROM (" + db.load_query("coverage_by_region")
                  + ") ORDER BY " + region_order_by)
    region_params = dict(params, q=region_query_text)

    # A download of the region table needs only that query, so it returns here
    # rather than falling through and fetching every country as well.
    if export_table == "region":
        response = exports.send(
            request.args.get("format"),
            "coverage_regions_%s_%s" % (antigen or "all", year or "all"),
            "Countries meeting the target, by region",
            "%s - %s" % (antigen or "all antigens", year or "all years"),
            REGION_COLUMNS, db.query(region_sql, region_params),
        )
        if response is not None:
            return response

    # The only concatenation allowed near SQL in this project. order_by can only
    # be one of the literal strings in SORT_KEYS.
    rows = db.query(db.load_query("coverage_by_country") + " ORDER BY " + order_by,
                    params)

    # An export is the whole filtered, sorted result -- never the page on
    # screen. It needs `rows` and nothing else, so it goes here: the three
    # aggregates below feed the banner, the region table and the chart, none of
    # which a download renders, and running them first meant every CSV paid for
    # three queries it threw away.
    response = exports.send(
        request.args.get("format"),
        "coverage_%s_%s" % (antigen or "all", year or "all"),
        "Vaccination rates by country",
        "%s - %s" % (antigen or "all antigens", year or "all years"),
        COLUMNS, rows,
    )
    if response is not None:
        return response

    summary = db.query_one(db.load_query("coverage_selection_summary"), params)
    outcome = db.query_one(db.load_query("coverage_outcome"), params)
    region_rows = db.query(region_sql, region_params)

    # The chart draws one column per region, so it needs the rolled-up shape --
    # a different query result from the table above it, which is why the two no
    # longer share a sort order.
    chart_rows = db.query(
        "SELECT * FROM (" + db.load_query("coverage_by_region") + ")",
        dict(region_params, detail=None))

    # WHO's own figure for this disease. Nothing on the page is filtered or
    # counted with it -- that is BRIEF_THRESHOLD's job -- it only fills the
    # citation in the method note, so it is looked up after the export branch
    # above, where a download would have paid for a row it never renders.
    threshold = None
    if antigen:
        threshold = db.query_one(db.load_query("threshold_for_antigen"),
                                 {"antigen": antigen})

    # Paginate the country table with a ?page= GET link so it works without
    # JavaScript and stays bookmarkable. The full `rows` is kept above, so an
    # export still contains every row.
    page = db.paginate(rows, request.args.get("page"), request.args.get("per_page"))
    if page["rejected"]:
        rejected.append("page or rows-per-page")

    # Its own page number, so paging one table never moves the other.
    rpage = db.paginate(region_rows, request.args.get("rpage"))
    if rpage["rejected"]:
        rejected.append("region table page")

    # Every link and form on the page builds its URL from this dict, so the
    # pager, the two tables' controls and the export links cannot disagree.
    table_args = {
        "antigen": antigen, "year": year, "region": region, "country": country,
        "sort": sort_active, "per_page": page["size"], "rsort": rsort_active,
        "submitted": 1,
        "q": query_text, "rq": region_query_text,
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

    # Chart geometry. Turning a rate into a bar height is display formatting,
    # so it belongs here and not in the SQL.
    #
    # Lowest coverage on the left. Sorted ascending the colours group
    # themselves -- below-target bars to the left, at-or-above to the right --
    # which is what replaced the threshold rule and the colour key.
    #
    # "Not classified" is left out. It is nine territories with no row in the
    # Country table, not a region, and charting it beside real regions invites
    # the reader to compare them. The TABLE still lists it, labelled, so the
    # anomaly is disclosed rather than dropped.
    chart_view = []
    for r in chart_rows:
        weighted = r["avg_weighted"]
        if weighted is None or r["region_id"] is None:
            continue
        chart_view.append({
            "row": r,
            "name": fix_region(r["region_name"]),
            "bar_pct": min(100.0, float(weighted)),
        })
    chart_view.sort(key=lambda item: item["row"]["avg_weighted"])

    region_view = [{"row": r, "name": fix_region(r["region_name"])}
                   for r in rpage["rows"]]

    return render_template(
        "pages/2a_coverage.html",
        db_missing=None, submitted=True,
        antigens=antigens, years=years, regions=regions, countries=countries,
        antigen=antigen, year=year, region=region, country=country,
        sort_active=sort_active, sort_labels=SORT_LABELS,
        rsort_active=rsort_active, region_sort_labels=REGION_SORT_LABELS,
        threshold_pct=BRIEF_THRESHOLD,
        query_text=query_text, region_query_text=region_query_text,
        # antigen code -> disease, so the region table can print "MCV1 . Measles"
        # without a per-row lookup in the template.
        disease_of={a["antigen"]: a["disease_name"] for a in antigens},
        summary=summary, outcome=outcome, region_view=region_view,
        chart_view=chart_view, rows=rows,
        page=page, rpage=rpage, table_args=table_args,
        pdf_ok=exports.pdf_available(),
        threshold=threshold, conflict=conflict, rejected=rejected,
        fix_region=fix_region,
        fmt_int=db.fmt_int, fmt_big=db.fmt_big, fmt_pct=db.fmt_pct,
        fmt_num=db.fmt_num,
    )
