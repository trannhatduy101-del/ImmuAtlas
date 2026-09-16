"""CSV and PDF export, shared by every result table on the site.

One column vocabulary, two renderers. A page declares its columns once:

    COLUMNS = [
        ("Country",    "country_name",      str),
        ("Coverage %", "coverage_reported", db.fmt_num),
    ]

each entry being (header, row key, formatter). The formatter is the SAME
callable the template uses, which is what stops the file and the screen from
disagreeing, and it is responsible for turning None into db.BLANK so a missing
value reads "no data" in both places rather than as an empty cell.

Exports always receive the full filtered+sorted result, never one page of it.
"""

import csv
import io
from urllib.parse import quote

from flask import Response

import db

FORMATS = ("csv", "pdf")


def _cell(row, key, fmt):
    """One formatted cell. A key the query does not return reads as no data
    rather than raising -- a typo in a COLUMNS table must not 500 a download."""
    try:
        value = row[key]
    except (KeyError, IndexError):
        value = None
    return fmt(value)


def _table(columns, rows):
    return [[_cell(row, key, fmt) for _, key, fmt in columns] for row in rows]


def _disposition(filename):
    """Content-Disposition with the filename BOTH quoted and UTF-8 encoded.

    The bare `filename=` form is what older clients read and must not contain a
    raw non-ASCII byte or a space; `filename*=` is what everything modern
    prefers. Sending both is the only combination that behaves everywhere.
    """
    ascii_name = filename.encode("ascii", "replace").decode("ascii")
    return 'attachment; filename="%s"; filename*=UTF-8\'\'%s' % (
        ascii_name, quote(filename)
    )


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def csv_response(stem, columns, rows):
    # newline="" is what the csv module asks for: without it the writer's own
    # \r\n line terminator gets translated again and every other row in Excel
    # comes out blank.
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow([header for header, _, _ in columns])
    writer.writerows(_table(columns, rows))

    # Excel decides the encoding of a .csv from its first bytes and assumes the
    # local codepage without this mark, which turns "Côte d'Ivoire" into
    # mojibake on exactly the countries this dataset is about.
    body = "﻿" + buf.getvalue()

    filename = stem + ".csv"
    return Response(
        body,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": _disposition(filename)},
    )


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def pdf_available():
    """Whether a PDF can be produced right now.

    Templates ask before offering the link. fpdf2 is a real dependency in
    requirements.txt, but a clone whose environment predates it must still run
    the whole site and still export CSV -- a missing optional library is not a
    reason for the application to be unusable.
    """
    try:
        import fpdf  # noqa: F401
    except ImportError:
        return False
    return True


def _latin1(text):
    """fpdf2's built-in fonts are Latin-1 only.

    Every country name in this dataset is representable in Latin-1, so nothing
    is lost today, but a name that is not must degrade to a replacement
    character instead of raising mid-download.
    """
    # ponytail: core font is Latin-1; embed a DejaVu TTF if a name outside it
    # ever appears (fpdf2 add_font + a .ttf in static/fonts/).
    return text.encode("latin-1", "replace").decode("latin-1")


def pdf_response(stem, title, subtitle, columns, rows):
    try:
        from fpdf import FPDF
    except ImportError:
        return Response(
            "PDF export needs the fpdf2 package.\n"
            "Install it with:  pip install -r requirements.txt\n"
            "The CSV export works without it.",
            status=503,
            mimetype="text/plain; charset=utf-8",
        )

    data = _table(columns, rows)

    # Landscape once a table is wide enough that portrait would crush the
    # country names, which are the column a reader scans.
    orientation = "L" if len(columns) > 4 else "P"
    pdf = FPDF(orientation=orientation, unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    usable = pdf.w - pdf.l_margin - pdf.r_margin
    # The first column holds names and gets double share; the rest are figures.
    shares = [2.0] + [1.0] * (len(columns) - 1)
    widths = [usable * s / sum(shares) for s in shares]
    row_h = 6.0
    bottom = pdf.h - pdf.b_margin

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, _latin1(title), new_x="LMARGIN", new_y="NEXT")
    if subtitle:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(90, 90, 90)
        pdf.cell(0, 5, _latin1(subtitle), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    def header():
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(8, 47, 73)       # --bg-deep, the site's heading band
        pdf.set_text_color(255, 255, 255)
        for (head, _, _), width in zip(columns, widths):
            pdf.cell(width, row_h, " " + _latin1(head), border=0, fill=True)
        pdf.ln(row_h)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 8)

    header()
    for index, line in enumerate(data):
        if pdf.get_y() + row_h > bottom:
            pdf.add_page()
            header()
        pdf.set_fill_color(244, 249, 253)   # --bg, the site's paper
        for text, width in zip(line, widths):
            pdf.cell(width, row_h, " " + _latin1(str(text)), border="B",
                     fill=index % 2 == 1)
        pdf.ln(row_h)

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(90, 90, 90)
    pdf.ln(2)
    pdf.cell(0, 4, _latin1("%d rows. Source: WHO Immunization Data portal."
                           % len(data)))

    filename = stem + ".pdf"
    return Response(
        bytes(pdf.output()),
        mimetype="application/pdf",
        headers={"Content-Disposition": _disposition(filename)},
    )


# ---------------------------------------------------------------------------
# Entry point used by the routes
# ---------------------------------------------------------------------------

def send(fmt, stem, title, subtitle, columns, rows):
    """Return a download Response, or None when this is an ordinary page view.

    Callers do:

        resp = exports.send(request.args.get("format"), ...)
        if resp is not None:
            return resp
    """
    if fmt == "csv":
        return csv_response(stem, columns, rows)
    if fmt == "pdf":
        return pdf_response(stem, title, subtitle, columns, rows)
    return None
