"""1B Mission statement -- Sub-Task B."""

from flask import Blueprint, render_template
from db import load_query, query

bp = Blueprint("mission", __name__)


@bp.route("/mission")
def index():
    team_members = query(load_query("team_members"))

    personas = [
        {
            "name": "Grace Achieng",
            "image": "img/Duy.png",
        },
        {
            "name": "Daniel Nguyen",
            "image": "img/Huy.png",
        },
    ]

    return render_template(
        "pages/1b_mission.html",
        team_members=team_members,
        personas=personas,
    )