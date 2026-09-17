"""
Regenerate src/worldmap.py from Natural Earth.

    python tools/build_worldmap.py

Run this once. It downloads the Natural Earth 1:110m country outlines, projects
every country onto a flat equirectangular map, and writes the result out as a
Python module of SVG path strings keyed by ISO 3166-1 alpha-3 code -- the same
codes the supplied WHO data uses for Country.CountryID, so the two join with no
lookup table in between.

Why a generated module rather than the GeoJSON itself:

  * The GeoJSON is 838 KB. The projected paths are 84 KB, because the projection
    throws away everything the page does not draw.
  * A module is imported once and cached by Python. Reading and parsing JSON on
    every request would repeat work whose answer never changes.
  * It keeps the running application offline. Nothing fetches anything at
    request time; this script is the only part that touches the network, and it
    is not imported by the app.

Natural Earth is public domain. Re-run this if the map ever needs more detail
(lower `STEP`) or a different resolution (`SOURCE`).
"""

import json
import os
import urllib.request

SOURCE = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector"
          "/master/geojson/ne_110m_admin_0_countries.geojson")

CREDIT = ("Natural Earth 1:110m Admin 0 Countries, public domain "
          "(naturalearthdata.com)")

# The flat map the sphere is wrapped in. 2:1 is what equirectangular wants:
# 360 degrees of longitude across, 180 of latitude down.
WIDTH, HEIGHT = 720, 360

# Keep every point. 110m is already the coarsest Natural Earth ships, and at
# this size dropping more would show as visibly straightened coastlines. Raise
# to 2 to halve the file if the page ever needs it.
STEP = 1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "src", "worldmap.py")


def project(lon, lat):
    """Longitude/latitude to a point on the flat map.

    Equirectangular, which is the projection a spinning texture needs: x depends
    only on longitude, so sliding the image sideways by one map width lands
    exactly back where it started and the loop cannot show a seam.
    """
    return ((lon + 180.0) / 360.0 * WIDTH,
            (90.0 - lat) / 180.0 * HEIGHT)


def iso_code(properties):
    """The country's ISO alpha-3 code, or None if it genuinely has none.

    ISO_A3 alone is not enough: Natural Earth stores -99 there for France and
    Norway, whose codes sit in ISO_A3_EH instead. Reading only the first field
    drops two countries out of the middle of the map, which is very visible.
    """
    for field in ("ISO_A3", "ISO_A3_EH", "ADM0_ISO"):
        value = (properties.get(field) or "").strip()
        if value and value != "-99":
            return value
    return None


def rings(geometry):
    """Every closed ring in a Polygon or MultiPolygon, outer and inner alike."""
    if geometry["type"] == "Polygon":
        polygons = [geometry["coordinates"]]
    else:
        polygons = geometry["coordinates"]
    for polygon in polygons:
        for ring in polygon:
            yield ring


def path_for(geometry):
    """One SVG `d` string for a country, or None when nothing survives.

    Coordinates are rounded to whole units. At 720x360 that is half a degree of
    longitude, far finer than the eye resolves on a 320px sphere, and it is what
    takes the file from 210 KB to 84 KB.
    """
    parts = []
    for ring in rings(geometry):
        points = []
        for lon, lat in ring[::STEP]:
            x, y = project(lon, lat)
            points.append("%d,%d" % (round(x), round(y)))
        # Two points cannot enclose an area; a ring that short is a rounding
        # artefact rather than a landmass.
        if len(points) > 2:
            parts.append("M" + "L".join(points) + "Z")
    return "".join(parts) or None


def build():
    print("Downloading %s" % SOURCE)
    with urllib.request.urlopen(SOURCE, timeout=60) as response:
        data = json.load(response)

    paths = {}
    skipped = []
    for feature in data["features"]:
        iso = iso_code(feature["properties"])
        # Natural Earth writes -99 where a feature has no code of its own, which
        # for Kosovo, Northern Cyprus and Somaliland is the honest answer: they
        # have no ISO 3166-1 code, so there is nothing in the WHO data to join
        # them to. Reported and left out rather than guessed at.
        if not iso:
            skipped.append(feature["properties"].get("ADMIN", "?"))
            continue
        d = path_for(feature["geometry"])
        if d:
            paths[iso] = d

    lines = [
        '"""',
        "World map outlines, projected for the globe on page 3A.",
        "",
        "GENERATED FILE -- do not edit by hand. Rebuild with:",
        "",
        "    python tools/build_worldmap.py",
        "",
        "Source: %s" % CREDIT,
        "",
        "Each value is an SVG path on a %dx%d equirectangular map, keyed by the"
        % (WIDTH, HEIGHT),
        "ISO 3166-1 alpha-3 code, which is what Country.CountryID holds.",
        '"""',
        "",
        "WIDTH = %d" % WIDTH,
        "HEIGHT = %d" % HEIGHT,
        "CREDIT = %r" % CREDIT,
        "",
        "PATHS = {",
    ]
    for iso in sorted(paths):
        lines.append("    %r: %r," % (iso, paths[iso]))
    lines.append("}")
    lines.append("")

    with open(OUTPUT, "w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines))

    size = os.path.getsize(OUTPUT)
    print("Wrote %s" % OUTPUT)
    print("  %d countries, %.0f KB" % (len(paths), size / 1024.0))
    if skipped:
        print("  %d features without an ISO code, left out: %s"
              % (len(skipped), ", ".join(sorted(skipped))))


if __name__ == "__main__":
    build()
