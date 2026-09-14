"""3B Countries above the global infection rate -- Sub-Task B."""

from flask import Blueprint, render_template, request

import db


bp = Blueprint("above_average", __name__)


def _validate(value, allowed_values):
    """Return the value if it is in the allowed list; otherwise return None."""
    if value is None:
        return None

    value = str(value).strip()

    allowed = {str(item) for item in allowed_values}

    return value if value in allowed else None


@bp.route("/above-average")
def index():
    # Load filter options directly from the database.
    infection_types = db.query(
        db.load_query("filter_infection_types")
    )

    years = db.query(
        db.load_query("filter_years")
    )

    # Get available values from the database.
    infection_type_values = [
        row["inf_type"] for row in infection_types
    ]

    year_values = [
        row["year"] for row in years
    ]

    # Read user selections.
    selected_infection = _validate(
        request.args.get("infection_type"),
        infection_type_values
    )

    selected_year_raw = request.args.get("year")

    selected_year = _validate(
        selected_year_raw,
        year_values
    )

    global_rate = None
    results = []

    if selected_infection and selected_year:
        params = {
            "infection_type": selected_infection,
            "year": int(selected_year),
        }

        # Calculate the population-weighted global infection rate.
        global_results = db.query(
            db.load_query("global_infection_rate"),
            params,
        )

        if global_results:
            global_rate = global_results[0]

        # Find countries whose rate is above the global rate.
        results = db.query(
            db.load_query("countries_above_global_rate"),
            params,
        )

    return render_template(
        "pages/3b_above_average.html",
        infection_types=infection_types,
        years=years,
        selected_infection=selected_infection,
        selected_year=selected_year,
        global_rate=global_rate,
        results=results,
    )