"""2B Focused infection view by economic status -- Sub-Task B."""

from flask import Blueprint, render_template, request

import db
import exports

bp = Blueprint("infections", __name__)


# Safe sorting options for the by-country table. The user picks a label; only
# these fixed SQL fragments can ever reach ORDER BY.
SORT_KEYS = {
    "rate_desc": "cases_per_100k IS NULL, cases_per_100k DESC, country_name ASC",
    "rate_asc": "cases_per_100k IS NULL, cases_per_100k ASC,  country_name ASC",
    "cases_desc": "cases DESC, country_name ASC",
    "cases_asc": "cases ASC,  country_name ASC",
    "population_desc": "national_population IS NULL, national_population DESC, country_name ASC",
    "population_asc": "national_population IS NULL, national_population ASC,  country_name ASC",
    # The Data column. Ordering on value_status alphabetically would sort by a
    # code the reader never sees; the question they are actually asking when
    # they sort that column is "which rows should I not trust", so the flagged
    # ones come first.
    "flagged_first": ("CASE WHEN value_status = 'suspicious_zero' THEN 0 ELSE 1 END, "
                      "country_name ASC"),
    "country_asc": "country_name ASC",
}
SORT_LABELS = [
    ("rate_desc", "Infection rate: highest first"),
    ("rate_asc", "Infection rate: lowest first"),
    ("cases_desc", "Cases: highest first"),
    ("cases_asc", "Cases: lowest first"),
    ("population_desc", "Population: largest first"),
    ("population_asc", "Population: smallest first"),
    ("flagged_first", "Flagged data first"),
    ("country_asc", "Country name"),
]
DEFAULT_SORT = "rate_desc"

# The all-phases table is five rows, so it gets a sort but no pager.
PHASE_SORT_KEYS = {
    "cases_desc": "total_cases DESC",
    "rate_desc": "infection_rate_per_100k IS NULL, infection_rate_per_100k DESC",
    "rate_asc": "infection_rate_per_100k IS NULL, infection_rate_per_100k ASC",
    "countries_desc": "country_count DESC, economy_phase ASC",
    "flagged_desc": "n_suspicious_zero DESC, economy_phase ASC",
    "phase": "economy_phase ASC",
}
PHASE_SORT_LABELS = [
    ("cases_desc", "Total cases: highest first"),
    ("rate_desc", "Rate: highest first"),
    ("rate_asc", "Rate: lowest first"),
    ("countries_desc", "Most countries first"),
    ("flagged_desc", "Most flagged first"),
    ("phase", "Economic phase"),
]
DEFAULT_PHASE_SORT = "cases_desc"

# Export columns. The formatter is the same one the template uses, so the file
# and the screen cannot disagree, and each one turns None into "no data".
COLUMNS = [
    ("Country", "country_name", str),
    ("Economic phase", "economy_phase", str),
    ("Disease", "disease_name", str),
    ("Year", "year", db.fmt_int),
    ("Reported cases", "cases", db.fmt_int),
    ("Population", "national_population", db.fmt_int),
    ("Cases per 100k", "cases_per_100k", db.fmt_num),
    ("Data status", "value_status", str),
]


@bp.route("/infections")
def index():
    try:
        economies = db.query(db.load_query("filter_economies"))
        infection_types = db.query(db.load_query("filter_infection_types"))
        years = db.query(db.load_query("filter_years"))
    except db.DatabaseMissing as exc:
        return render_template("pages/2b_infections.html", db_missing=str(exc)), 503

    valid_economies = {row["economy_phase"] for row in economies}
    valid_infections = {row["inf_type"] for row in infection_types}
    valid_years = {row["year"] for row in years}

    # A value that is not on the list never reaches the database, and the fact
    # that it was dropped is reported rather than silently widening the view.
    rejected = []
    selected_economy, bad = db.validate(request.args.get("economy"), valid_economies)
    if bad:
        rejected.append("economic status")
    selected_infection, bad = db.validate(
        request.args.get("infection_type"), valid_infections)
    if bad:
        rejected.append("infection type")
    selected_year, bad = db.validate(request.args.get("year"), valid_years, int)
    if bad:
        rejected.append("year")

    sort = request.args.get("sort")
    order_by = db.safe_order_by(sort, SORT_KEYS, DEFAULT_SORT)
    selected_sort = sort if sort in SORT_KEYS else DEFAULT_SORT
    if sort is not None and sort not in SORT_KEYS:
        rejected.append("sort order")

    phase_sort = request.args.get("esort")
    phase_order_by = db.safe_order_by(phase_sort, PHASE_SORT_KEYS, DEFAULT_PHASE_SORT)
    selected_phase_sort = (phase_sort if phase_sort in PHASE_SORT_KEYS
                           else DEFAULT_PHASE_SORT)
    if phase_sort is not None and phase_sort not in PHASE_SORT_KEYS:
        rejected.append("phase sort order")

    results = []
    summary = None
    all_economies_summary = []
    chart_results = []
    page = db.paginate([], None)

    # Every link and form on the page is built from this dict, so the pager,
    # the table controls and the export links can never disagree about the
    # current selection.
    table_args = {
        "economy": selected_economy,
        "infection_type": selected_infection,
        "year": selected_year,
        "sort": selected_sort,
        "per_page": request.args.get("per_page"),
        "esort": selected_phase_sort,
    }

    if selected_economy and selected_infection and selected_year:
        params = {
            "economy": selected_economy,
            "infection_type": selected_infection,
            "year": int(selected_year),
        }

        # order_by can only be one of the literal strings in SORT_KEYS.
        results = db.query(
            db.load_query("infections_by_economy") + " ORDER BY " + order_by,
            params,
        )

        # The export always gets the full filtered result, never one page.
        response = exports.send(
            request.args.get("format"),
            "infections_%s_%s_%s" % (
                selected_economy.replace(" ", "-").lower(),
                selected_infection, selected_year),
            "Infections by economic status",
            "%s - %s - %s" % (selected_economy, selected_infection, selected_year),
            COLUMNS, results,
        )
        if response is not None:
            return response

        summary = db.query_one(db.load_query("infections_economy_summary"), params)

        all_economies_summary = db.query(
            db.load_query("infections_all_economies_summary")
            + " ORDER BY " + phase_order_by,
            params,
        )

        chart_results = db.query(db.load_query("infections_economy_chart"), params)

        page = db.paginate(results, request.args.get("page"),
                           request.args.get("per_page"))
        if page["rejected"]:
            rejected.append("page or rows-per-page")
        table_args["per_page"] = page["size"]

    return render_template(
        "pages/2b_infections.html",
        db_missing=None,
        economies=economies,
        infection_types=infection_types,
        years=years,
        selected_economy=selected_economy,
        selected_infection=selected_infection,
        selected_year=selected_year,
        selected_sort=selected_sort,
        sort_options=SORT_LABELS,
        selected_phase_sort=selected_phase_sort,
        phase_sort_options=PHASE_SORT_LABELS,
        rejected=rejected,
        results=results,
        summary=summary,
        all_economies_summary=all_economies_summary,
        chart_results=chart_results,
        page=page,
        table_args=table_args,
        pdf_ok=exports.pdf_available(),
        fmt_int=db.fmt_int,
        fmt_big=db.fmt_big,
        fmt_pct=db.fmt_pct,
        fmt_num=db.fmt_num,
    )
