"""1B Mission statement -- Sub-Task B.

Not built yet. Renders an honest "not finished" page so the route and the nav
link stay live (CLAUDE.md section 8, "All six pages reachable").
"""

from flask import Blueprint, render_template

bp = Blueprint("mission", __name__)


@bp.route("/mission")
def index():
    return render_template("pages/1b_mission.html")
