"""2B Infection data by economic status -- Sub-Task B.

Not built yet. Renders an honest "not finished" page so the route and the nav
link stay live (CLAUDE.md section 8, "All six pages reachable").
"""

from flask import Blueprint, render_template

bp = Blueprint("infections", __name__)


@bp.route("/infections")
def index():
    return render_template("pages/2b_infections.html")
