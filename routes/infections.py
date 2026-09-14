"""2B Infection data by economic status -- Sub-Task B.

Allows the user to select one economic status, infection type and year.
SQL performs filtering, aggregation, calculation and sorting. Python validates
request values and formats data for presentation.
"""

from flask import Blueprint, render_template, request

import db


bp = Blueprint("infections", __name__, url_prefix="/infections")


SORT_KEYS = {
    "rate_desc": "cases_per_100k IS NULL, cases_per_100k DESC, country_name ASC",
    "rate_asc": "cases_per_100k IS NULL, cases_per_100k ASC, country_name ASC",
    "cases_desc": "cases IS NULL, cases DESC, country_name ASC",
    "cases_asc": "cases IS NULL, cases ASC, country_name ASC",
    "population_desc": "national_population IS NULL, national_population DESC, country_name ASC",
    "country": "country_name ASC",
}

SORT_LABELS = [
    ("rate_desc", "Infection rate, highest first"),
    ("rate_asc", "Infection rate, lowest first"),
    ("cases_desc", "Cases, highest first"),
    ("cases_asc", "Cases, lowest first"),
    ("population_desc", "Population, largest first"),
    ("country", "Country name"),
]

DEFAULT_SORT = "rate_desc"


def _validate(raw, allowed, cast=str):
    """Validate a request value against values offered by the database."""
    if raw is None or raw == "":
        return None, False

    try:
        value = cast(raw)
    except (TypeError, ValueError):
        return None, True

    if value in allowed:
        return value, False

    return None, True


@bp.route("/")
def index():
    try:
        economies = db.query(db.load_query("filter_economies"))
        infection_types = db.query(db.load_query("filter_infection_types"))
        years = db.query(db.load_query("filter_years"))
    except db.DatabaseMissing as exc:
        return render_template(
            "pages/2b_infections.html",
            db_missing=str(exc)
        ), 503

    valid_economies = {
        row["economy_phase"] for row in economies
    }

    valid_infection_types = {
        row["inf_type"] for row in infection_types
    }

    valid_years = {
        row["year"] for row in years
    }

    rejected = []

    economy, bad = _validate(
        request.args.get("economy"),
        valid_economies
    )
    if bad:
        rejected.append("economic status")

    infection_type, bad = _validate(
        request.args.get("infection_type"),
        valid_infection_types
    )
    if bad:
        rejected.append("infection type")

    year, bad = _validate(
        request.args.get("year"),
        valid_years,
        int
    )
    if bad:
        rejected.append("year")

    requested_sort = request.args.get("sort")
    order_by = db.safe_order_by(
        requested_sort,
        SORT_KEYS,
        DEFAULT_SORT
    )

    sort_active = (
        requested_sort
        if requested_sort in SORT_KEYS
        else DEFAULT_SORT
    )

    if requested_sort is not None and requested_sort not in SORT_KEYS:
        rejected.append("sort order")

    results = []
    summary = None

    if economy and infection_type and year:
        params = {
            "economy": economy,
            "infection_type": infection_type,
            "year": year,
        }

        sql = (
            db.load_query("infections_by_economy")
            + " ORDER BY "
            + order_by
        )

        results = db.query(sql, params)

        summary = db.query_one(
            db.load_query("infections_economy_summary"),
            params
        )

    return render_template(
        "pages/2b_infections.html",
        db_missing=None,
        economies=economies,
        infection_types=infection_types,
        years=years,
        results=results,
        summary=summary,
        selected_economy=economy,
        selected_infection=infection_type,
        selected_year=year,
        sort_active=sort_active,
        sort_labels=SORT_LABELS,
        rejected=rejected,
        fmt_int=db.fmt_int,
    )