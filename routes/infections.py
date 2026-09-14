"""2B Focused infection view by economic status -- Sub-Task B."""

from flask import Blueprint, render_template, request

import db

bp = Blueprint("infections", __name__)


def _validate(value, allowed_values):
    """Return the value if it is in the allowed list; otherwise return None."""
    if value is None:
        return None

    value = str(value).strip()
    allowed = {str(item) for item in allowed_values}

    return value if value in allowed else None


# Safe sorting options.
# The user selects a label, but only these predefined SQL fragments
# are allowed to reach the ORDER BY clause.
SORT_KEYS = {
    "rate_desc": "cases_per_100k DESC",
    "rate_asc": "cases_per_100k ASC",
    "cases_desc": "cases DESC",
    "cases_asc": "cases ASC",
    "country_asc": "country_name ASC",
}

SORT_LABELS = {
    "rate_desc": "Infection rate: highest first",
    "rate_asc": "Infection rate: lowest first",
    "cases_desc": "Cases: highest first",
    "cases_asc": "Cases: lowest first",
    "country_asc": "Country name",
}

DEFAULT_SORT = "rate_desc"


@bp.route("/infections")
def index():
    # ---------------------------------------------------------
    # 1. Load filter options from the database
    # ---------------------------------------------------------

    economies = db.query(
        db.load_query("filter_economies")
    )

    infection_types = db.query(
        db.load_query("filter_infection_types")
    )

    years = db.query(
        db.load_query("filter_years")
    )

    # ---------------------------------------------------------
    # 2. Get the values submitted by the user
    # ---------------------------------------------------------

    selected_economy = _validate(
        request.args.get("economy"),
        [row["economy_phase"] for row in economies],
    )

    selected_infection = _validate(
        request.args.get("infection_type"),
        [row["inf_type"] for row in infection_types],
    )

    selected_year = _validate(
        request.args.get("year"),
        [row["year"] for row in years],
    )

    selected_sort = _validate(
        request.args.get("sort"),
        SORT_KEYS.keys(),
    )

    if selected_sort is None:
        selected_sort = DEFAULT_SORT

    # ---------------------------------------------------------
    # 3. Prepare empty results
    # ---------------------------------------------------------

    results = []
    summary = None

    # NEW:
    # These results will be used for the visualisation/chart.
    chart_results = []

    # ---------------------------------------------------------
    # 4. Only query the main data when all filters are valid
    # ---------------------------------------------------------

    if (
        selected_economy
        and selected_infection
        and selected_year
    ):
        params = {
            "economy": selected_economy,
            "infection_type": selected_infection,
            "year": int(selected_year),
        }

        # -----------------------------------------------------
        # Main result table
        # -----------------------------------------------------

        order_by = SORT_KEYS[selected_sort]

        sql = (
            db.load_query("infections_by_economy")
            + " ORDER BY "
            + order_by
        )

        results = db.query(
            sql,
            params,
        )

        # -----------------------------------------------------
        # Summary information
        # -----------------------------------------------------

        summary_results = db.query(
            db.load_query("infections_economy_summary"),
            params,
        )

        if summary_results:
            summary = summary_results[0]

        # -----------------------------------------------------
        # NEW: Data for the visualisation
        # -----------------------------------------------------
        #
        # This query gets the Top 10 countries with the
        # highest infection rate for the selected filters.
        #
        # IMPORTANT:
        # This is separate from the main table so the user can
        # still choose any sorting method for the table.
        # -----------------------------------------------------

        chart_results = db.query(
            db.load_query("infections_economy_chart"),
            params,
        )

    # ---------------------------------------------------------
    # 5. Render the page
    # ---------------------------------------------------------

    return render_template(
        "pages/2b_infections.html",

        # Filter options
        economies=economies,
        infection_types=infection_types,
        years=years,

        # Selected filters
        selected_economy=selected_economy,
        selected_infection=selected_infection,
        selected_year=selected_year,

        # Sorting
        selected_sort=selected_sort,
        sort_options=SORT_LABELS,

        # Main page data
        results=results,
        summary=summary,

        # NEW:
        # Send Top 10 chart data to the HTML template.
        chart_results=chart_results,
    )