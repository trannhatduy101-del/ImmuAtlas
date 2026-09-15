"""3B Countries above the global infection rate -- Sub-Task B."""

from flask import Blueprint, render_template, request

import db


bp = Blueprint("above_average", __name__)

# Level 3 requires results to sort "by a user-selected criterion". Written out
# in full rather than built from the column name, because a column name is an
# identifier, not a value, and cannot be bound as a query parameter.
SORT_KEYS = {
    "rate_desc":  "country_rate_per_100k DESC, country_name ASC",
    "rate_asc":   "country_rate_per_100k ASC,  country_name ASC",
    "cases_desc": "total_cases DESC, country_name ASC",
    "population_desc": "population IS NULL, population DESC, country_name ASC",
    "country":    "country_name ASC",
}
SORT_LABELS = [
    ("rate_desc",  "Rate, highest first"),
    ("rate_asc",   "Rate, lowest first"),
    ("cases_desc", "Reported cases, highest first"),
    ("population_desc", "Population, largest first"),
    ("country",    "Country name"),
]
DEFAULT_SORT = "rate_desc"


def _validate(value, allowed_values):
    """Return the value if it is in the allowed list; otherwise return None."""
    if value is None:
        return None

    value = str(value).strip()
    allowed = {str(item) for item in allowed_values}

    return value if value in allowed else None


@bp.route("/above-average")
def index():
    # Load filter options from the database
    infection_types = db.query(
        db.load_query("filter_infection_types")
    )

    years = db.query(
        db.load_query("filter_years")
    )

    # Create lists of valid values for validation
    infection_type_values = [
        row["inf_type"]
        for row in infection_types
    ]

    year_values = [
        row["year"]
        for row in years
    ]

    # Validate user selections
    selected_infection = _validate(
        request.args.get("infection_type"),
        infection_type_values
    )

    selected_year_raw = request.args.get("year")

    selected_year = _validate(
        selected_year_raw,
        year_values
    )

    sort = request.args.get("sort")
    selected_sort = sort if sort in SORT_KEYS else DEFAULT_SORT
    order_by = db.safe_order_by(sort, SORT_KEYS, DEFAULT_SORT)

    # Default values
    global_rate = None
    results = []
    chart_results = []

    # Run queries only when both filters are valid
    if selected_infection and selected_year:

        params = {
            "infection_type": selected_infection,
            "year": int(selected_year),
        }

        # Calculate the global infection rate
        global_results = db.query(
            db.load_query("global_infection_rate"),
            params,
        )

        if global_results:
            global_rate = global_results[0]

        # Find countries above the global infection rate. order_by can only be
        # one of the literal strings in SORT_KEYS (db.safe_order_by), so this
        # concatenation is safe -- nothing from the request reaches the SQL text.
        results = db.query(
            db.load_query("countries_above_global_rate") + " ORDER BY " + order_by,
            params,
        )

        # Get Top 10 countries for the chart
        chart_results = db.query(
            db.load_query("countries_above_global_chart"),
            params,
        )

    return render_template(
        "pages/3b_above_average.html",
        infection_types=infection_types,
        years=years,
        selected_infection=selected_infection,
        selected_year=selected_year,
        selected_sort=selected_sort,
        sort_labels=SORT_LABELS,
        global_rate=global_rate,
        results=results,
        chart_results=chart_results,

        # Display formatters, shared with the Sub-Task A pages so the whole
        # site formats numbers the same way.
        fmt_int=db.fmt_int,
        fmt_big=db.fmt_big,
        fmt_pct=db.fmt_pct,
    )