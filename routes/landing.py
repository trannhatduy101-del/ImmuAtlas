"""1A Landing page -- Sub-Task A.

Four facts, a 25-year trend, the diseases covered with their sourced thresholds,
and a block saying what the data cannot tell you. Every figure comes from a
query in queries/; nothing on this page is a literal typed into a template
(CLAUDE.md rule 7.2, verified by the mutation test in section 9).
"""

from flask import Blueprint, render_template

import db

bp = Blueprint("landing", __name__)

# The trend chart is drawn as inline SVG with the geometry computed here.
# Turning a value into a pixel is display formatting, which CLAUDE.md section 7
# puts in Python; the averaging behind it already happened in SQL.
CHART_W, CHART_H = 720, 200
PAD_L, PAD_R, PAD_T, PAD_B = 8, 8, 12, 26


def _trend_geometry(rows):
    """Turn the trend rows into SVG coordinates plus the axis bounds used.

    The y axis is deliberately NOT drawn from zero: an 82-to-89 movement is
    invisible on a 0-100 axis. A truncated axis exaggerates, so the bounds it
    actually used are returned and printed beside the chart. State the zoom,
    do not hide it.
    """
    points = [r for r in rows if r["avg_coverage"] is not None]
    if len(points) < 2:
        return None

    values = [float(r["avg_coverage"]) for r in points]
    y_min = max(0, int(min(values)) - 5)
    y_max = 100
    span = y_max - y_min or 1

    plot_w = CHART_W - PAD_L - PAD_R
    plot_h = CHART_H - PAD_T - PAD_B
    last = len(points) - 1

    coords = []
    for i, row in enumerate(points):
        x = PAD_L + (plot_w * i / last)
        y = PAD_T + plot_h * (1 - (float(row["avg_coverage"]) - y_min) / span)
        coords.append((round(x, 1), round(y, 1), row))

    return {
        "polyline": " ".join("%s,%s" % (x, y) for x, y, _ in coords),
        "coords": coords,
        "y_min": y_min,
        "y_max": y_max,
        "first": points[0],
        "last": points[-1],
    }


@bp.route("/")
def index():
    try:
        facts = db.query_one(db.load_query("landing_facts"))
        trend = db.query(db.load_query("landing_trend"))
        diseases = db.query(db.load_query("landing_diseases"))
        caveats = db.query_one(db.load_query("landing_data_caveats"))
    except db.DatabaseMissing as exc:
        # An honest empty state, never a blank page and never a stale number.
        return render_template("pages/1a_landing.html", db_missing=str(exc)), 503

    return render_template(
        "pages/1a_landing.html",
        db_missing=None,
        facts=facts,
        trend=trend,
        chart=_trend_geometry(trend),
        diseases=diseases,
        caveats=caveats,
        chart_w=CHART_W,
        chart_h=CHART_H,
        fmt_int=db.fmt_int,
        fmt_big=db.fmt_big,
        fmt_pct=db.fmt_pct,
    )
