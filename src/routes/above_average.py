"""3B Countries above the global infection rate -- Sub-Task B."""

from flask import Blueprint, render_template, request

import db
import exports

bp = Blueprint("above_average", __name__)

# Level 3 requires results to sort "by a user-selected criterion". Written out
# in full rather than built from the column name, because a column name is an
# identifier, not a value, and cannot be bound as a query parameter.
SORT_KEYS = {
    "rate_desc": "country_rate_per_100k DESC, country_name ASC",
    "rate_asc": "country_rate_per_100k ASC,  country_name ASC",
    "cases_desc": "total_cases DESC, country_name ASC",
    "population_desc": "population IS NULL, population DESC, country_name ASC",
    "country": "country_name ASC",
}
SORT_LABELS = [
    ("rate_desc", "Rate, highest first"),
    ("rate_asc", "Rate, lowest first"),
    ("cases_desc", "Reported cases, highest first"),
    ("population_desc", "Population, largest first"),
    ("country", "Country name"),
]
DEFAULT_SORT = "rate_desc"

COLUMNS = [
    ("Country", "country_name", str),
    ("Disease", "disease_name", str),
    ("Year", "year", db.fmt_int),
    ("Reported cases", "total_cases", db.fmt_int),
    ("Population", "population", db.fmt_int),
    ("Cases per 100k", "country_rate_per_100k", db.fmt_num),
]


@bp.route("/above-average")
def index():
    try:
        infection_types = db.query(db.load_query("filter_infection_types"))
        years = db.query(db.load_query("filter_years"))
    except db.DatabaseMissing as exc:
        return render_template("pages/3b_above_average.html", db_missing=str(exc)), 503

    valid_infections = {row["inf_type"] for row in infection_types}
    valid_years = {row["year"] for row in years}

    rejected = []
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

    global_rate = None
    results = []
    chart_results = []
    page = db.paginate([], None)

    table_args = {
        "infection_type": selected_infection,
        "year": selected_year,
        "sort": selected_sort,
        "per_page": request.args.get("per_page"),
    }

    if selected_infection and selected_year:
        params = {"infection_type": selected_infection, "year": int(selected_year)}

        # One row by construction: the WHERE pins a single inf_type and
        # disease_name is that type's description, so the GROUP BY can only
        # ever produce one group. query_one states that; indexing [0] hid it.
        global_rate = db.query_one(db.load_query("global_infection_rate"), params)

        # order_by can only be one of the literal strings in SORT_KEYS, so this
        # concatenation carries nothing the user typed.
        results = db.query(
            db.load_query("countries_above_global_rate") + " ORDER BY " + order_by,
            params,
        )

        response = exports.send(
            request.args.get("format"),
            "above_global_rate_%s_%s" % (selected_infection, selected_year),
            "Countries above the global infection rate",
            "%s - %s - global rate %s per 100k" % (
                selected_infection, selected_year,
                db.fmt_num(global_rate["global_rate_per_100k"])
                if global_rate else db.BLANK),
            COLUMNS, results,
        )
        if response is not None:
            return response

        chart_results = db.query(db.load_query("countries_above_global_chart"), params)

        page = db.paginate(results, request.args.get("page"),
                           request.args.get("per_page"))
        if page["rejected"]:
            rejected.append("page or rows-per-page")
        table_args["per_page"] = page["size"]

    return render_template(
        "pages/3b_above_average.html",
        db_missing=None,
        # Gates the "next page" card in base.html, on the same values the page
        # checks before it drops the prompt.
        submitted=bool(selected_infection and selected_year and global_rate),
        infection_types=infection_types,
        years=years,
        selected_infection=selected_infection,
        selected_year=selected_year,
        selected_sort=selected_sort,
        sort_labels=SORT_LABELS,
        rejected=rejected,
        global_rate=global_rate,
        results=results,
        chart_results=chart_results,
        page=page,
        table_args=table_args,
        pdf_ok=exports.pdf_available(),
        fmt_int=db.fmt_int,
        fmt_big=db.fmt_big,
        fmt_pct=db.fmt_pct,
        fmt_num=db.fmt_num,
    )
