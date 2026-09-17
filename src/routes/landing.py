"""1A Landing page -- Sub-Task A.

Four facts, a 25-year trend, the diseases covered with their sourced thresholds,
and a block saying what the data cannot tell you. Every figure comes from a
query in queries/; nothing on this page is a literal typed into a template
(the project spec rule 7.2, verified by the mutation test in section 9).
"""

from flask import Blueprint, render_template

import db
from routes.coverage import fix_region

bp = Blueprint("landing", __name__)

# Ring geometry for the "impact by region" cards: a fixed-radius circle, with
# the stroke-dasharray computed here (pixel math is display formatting) so the
# template only ever plugs in numbers already sized.
RING_R = 42
RING_C = round(2 * 3.14159265 * RING_R, 2)


def _ring(pct):
    """Stroke-dasharray/offset for a ring showing `pct` (0-100) filled."""
    pct = max(0.0, min(100.0, pct))
    filled = round(RING_C * pct / 100, 2)
    return {"r": RING_R, "circumference": RING_C, "filled": filled}

# The trend chart is drawn as inline SVG with the geometry computed here.
# Turning a value into a pixel is display formatting, which the project spec section 7
# puts in Python; the averaging behind it already happened in SQL.
# Roomy left/bottom padding leaves space for a real Y axis (coverage %) and X
# axis (year) with labels.
CHART_W, CHART_H = 720, 300
PAD_L, PAD_R, PAD_T, PAD_B = 52, 18, 18, 46

# Hover tooltip box, in the same user units as everything else above. The
# template draws a rect of exactly this size, so the two must agree or the text
# will sit outside its own background.
TIP_W, TIP_H = 76, 34


def _trend_geometry(rows):
    """Turn the trend rows into SVG coordinates, axis bounds, and labelled ticks.

    The y axis is deliberately NOT drawn from zero: an 82-to-89 movement is
    invisible on a 0-100 axis. A truncated axis exaggerates, so the bounds it
    actually used are shown as labelled Y ticks and stated beside the chart.
    State the zoom, do not hide it.
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

    def xpix(i):
        return PAD_L + plot_w * i / last

    def ypix(v):
        return PAD_T + plot_h * (1 - (v - y_min) / span)

    # Each point carries its own tooltip anchor, worked out here rather than in
    # the template. An SVG clips to its viewBox, so a tip centred on the first
    # or last dot would be sliced in half by the edge; and one sitting above the
    # highest dot would be cut off by the top. Both are decided from the point's
    # position, which is a layout calculation and belongs in Python.
    coords = []
    left_limit = PAD_L
    right_limit = CHART_W - PAD_R - TIP_W
    for i, r in enumerate(points):
        x = round(xpix(i), 1)
        y = round(ypix(float(r["avg_coverage"])), 1)
        # The tooltip box, positioned by its LEFT edge and clamped inside the
        # plot. Centring it on the dot and letting it fall where it may would
        # slice the first and last tips in half: an SVG clips to its viewBox.
        # The text is then centred inside the box, so box and text cannot
        # disagree about where the tip sits.
        tip_x = min(max(x - TIP_W / 2, left_limit), right_limit)
        # Above the dot by default, below it when the dot is too near the top.
        tip_y = y + 12 if y - TIP_H - 10 < PAD_T else y - TIP_H - 10
        coords.append({"x": x, "y": y, "row": r,
                       "tip_x": round(tip_x, 1),
                       "tip_y": round(tip_y, 1),
                       "tip_mid": round(tip_x + TIP_W / 2, 1)})

    # Y ticks: five evenly spaced coverage values from y_min to y_max (100).
    y_ticks = [{"y": round(ypix(y_min + span * k / 4), 1),
                "label": int(round(y_min + span * k / 4))}
               for k in range(5)]

    # X ticks: up to six years spread across the period, always incl. first/last.
    n = min(6, len(points))
    x_ticks = []
    for k in range(n):
        idx = round((len(points) - 1) * k / (n - 1)) if n > 1 else 0
        x_ticks.append({"x": round(xpix(idx), 1), "label": points[idx]["year"]})

    return {
        "polyline": " ".join("%s,%s" % (c["x"], c["y"]) for c in coords),
        "coords": coords,
        "y_min": y_min,
        "y_max": y_max,
        "first": points[0],
        "last": points[-1],
        "x_ticks": x_ticks,
        "y_ticks": y_ticks,
        "tip_w": TIP_W,
        "tip_h": TIP_H,
        "plot_left": PAD_L,
        "plot_right": CHART_W - PAD_R,
        "plot_top": PAD_T,
        "plot_bottom": CHART_H - PAD_B,
    }


@bp.route("/")
def index():
    try:
        facts = db.query_one(db.load_query("landing_facts"))
        trend = db.query(db.load_query("landing_trend"))
        diseases = db.query(db.load_query("landing_diseases"))
        caveats = db.query_one(db.load_query("landing_data_caveats"))
        # Unfiltered regional summary (every antigen, every year), so the
        # landing page can show impact BY REGION -- a different lens from the
        # global aggregate in "Four figures" and the year-by-year trend.
        region_base = db.load_query("coverage_by_region").rstrip().rstrip(";")
        region_sql = "SELECT * FROM (" + region_base + ") ORDER BY avg_weighted DESC"
        # threshold is None here on purpose: a threshold belongs to one disease,
        # and this call deliberately spans every antigen, so there is no single
        # bar to measure against. n_met_threshold comes back 0 and is not shown.
        regions = db.query(region_sql, {"antigen": None, "year": None,
                                        "country": None, "region": None,
                                        "threshold": None})
    except db.DatabaseMissing as exc:
        # An honest empty state, never a blank page and never a stale number.
        return render_template("pages/1a_landing.html", db_missing=str(exc)), 503

    # "Not classified" is territories with no region entry, not a real region
    # (the project spec 4.4) -- excluded from a leader/laggard comparison, which needs
    # two real regions to mean anything.
    real_regions = [r for r in regions
                    if r["region_id"] is not None and r["avg_weighted"] is not None]
    impact_regions = None
    if len(real_regions) >= 2:
        leading, behind = real_regions[0], real_regions[-1]
        gap = round(leading["avg_weighted"] - behind["avg_weighted"], 1)
        impact_regions = {
            "n_regions": len(real_regions),
            "leading": leading, "leading_name": fix_region(leading["region_name"]),
            "leading_ring": _ring(leading["avg_weighted"]),
            "behind": behind, "behind_name": fix_region(behind["region_name"]),
            "behind_ring": _ring(behind["avg_weighted"]),
            "gap": gap, "gap_ring": _ring(gap),
        }

    return render_template(
        "pages/1a_landing.html",
        db_missing=None,
        facts=facts,
        trend=trend,
        chart=_trend_geometry(trend),
        diseases=diseases,
        caveats=caveats,
        impact_regions=impact_regions,
        chart_w=CHART_W,
        chart_h=CHART_H,
        fmt_int=db.fmt_int,
        fmt_big=db.fmt_big,
        fmt_pct=db.fmt_pct,
    )
