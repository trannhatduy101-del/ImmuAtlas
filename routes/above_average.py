"""3B Countries above the global rate -- Sub-Task B.

Not built yet. Renders an honest "not finished" page so the route and the nav
link stay live (CLAUDE.md section 8, "All six pages reachable").
"""

from flask import Blueprint, render_template

bp = Blueprint("above_average", __name__)


@bp.route("/above-average")
def index():
    return render_template("pages/3b_above_average.html")
