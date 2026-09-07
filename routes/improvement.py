"""3A Biggest improvement in coverage -- Sub-Task A.

Not built yet. Renders an honest "not finished" page so the route and the nav
link stay live (CLAUDE.md section 8, "All six pages reachable").
"""

from flask import Blueprint, render_template

bp = Blueprint("improvement", __name__)


@bp.route("/improvement")
def index():
    return render_template("pages/3a_improvement.html")
