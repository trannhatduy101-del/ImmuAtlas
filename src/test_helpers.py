"""Checks for the pure helpers behind paging, validation and export.

Plain asserts, no framework -- the project has no test dependency and does not
need one for this. These cover the arithmetic and the file-format details that
a browser will NOT show you: an off-by-one in the page slice looks like a
perfectly normal table, and a missing byte-order mark looks fine until someone
opens the CSV in Excel.

    python src/test_helpers.py
"""

import db
import exports


def check_paginate():
    rows = list(range(1, 21))          # 20 rows

    empty = db.paginate([], None)
    assert empty["rows"] == [] and empty["total"] == 0
    assert empty["pages"] == 1, "an empty table is still page 1 of 1, never 0"
    assert empty["first"] == 0 and empty["last"] == 0

    # Sizes are whitelisted, so a size the caller does not offer is not usable
    # even in a test -- pass the allowed set explicitly to exercise the
    # arithmetic on its own.
    tens = dict(sizes=(10,), default_size=10)
    exact = db.paginate(rows, 2, 10, **tens)   # 20 rows, 10 a page -> 2 pages
    assert exact["pages"] == 2 and exact["rows"] == list(range(11, 21))
    assert exact["first"] == 11 and exact["last"] == 20

    partial = db.paginate(rows, 3, 8)  # 20 rows, 8 a page -> last page holds 4
    assert partial["pages"] == 3 and partial["rows"] == [17, 18, 19, 20]
    assert partial["first"] == 17 and partial["last"] == 20

    # Out-of-range and unparseable pages clamp instead of erroring: a stale
    # bookmark should show the nearest real page, not a 404 or a blank table.
    assert db.paginate(rows, 0, 8)["page"] == 1
    assert db.paginate(rows, 999, 8)["page"] == 3
    assert db.paginate(rows, "abc", 8)["page"] == 1
    assert db.paginate(rows, "abc", 8)["rejected"] is True
    assert db.paginate(rows, -5, 8)["page"] == 1

    # A page size we do not offer falls back to the default AND is reported,
    # so the page can say the control was ignored rather than silently
    # showing a different number of rows than the reader asked for.
    bad = db.paginate(rows, 1, 99)
    assert bad["size"] == db.DEFAULT_PAGE_SIZE and bad["rejected"] is True
    assert db.paginate(rows, 1, 25)["rejected"] is False

    # The property that actually matters: walking every page reproduces the
    # input exactly. No row may be dropped between pages or shown on two.
    for size in db.PAGE_SIZES:
        seen = []
        first = db.paginate(rows, 1, size)
        for n in range(1, first["pages"] + 1):
            seen.extend(db.paginate(rows, n, size)["rows"])
        assert seen == rows, "page size %d loses or repeats rows" % size


def check_validate():
    allowed = {"a", "b"}
    assert db.validate(None, allowed) == (None, False), "absent is not an error"
    assert db.validate("", allowed) == (None, False), "empty is not an error"
    assert db.validate("a", allowed) == ("a", False)
    # Present but not offered: dropped AND reported, because dropping a filter
    # widens the selection and the reader has to be told.
    assert db.validate("z", allowed) == (None, True)
    assert db.validate("x", {1, 2}, int) == (None, True), "uncastable is rejected"
    assert db.validate("2", {1, 2}, int) == (2, False), "cast before comparing"


def check_fmt_num():
    assert db.fmt_num(None) == db.BLANK
    assert db.fmt_num("") == db.BLANK
    assert db.fmt_num("not a number") == db.BLANK
    assert db.fmt_num(0) == "0.00"
    assert db.fmt_num(12.3456) == "12.35"
    assert db.fmt_num(12.3456, 1) == "12.3"
    # No thousands separator: a grouped number lands in a spreadsheet as text.
    assert "," not in db.fmt_num(1234567.5)


def check_csv():
    columns = [("Country", "country_name", str),
               ("Rate", "rate", db.fmt_num)]
    rows = [{"country_name": "Côte d'Ivoire", "rate": 12.345},
            {"country_name": "Nauru", "rate": None}]

    body = exports.csv_response("x", columns, rows).get_data(as_text=True)

    # Excel guesses the encoding from the first bytes and assumes the local
    # codepage without this mark, which mangles exactly the country names this
    # dataset is about.
    assert body.startswith("﻿"), "CSV must start with a UTF-8 BOM"
    assert "Côte d'Ivoire" in body
    assert "12.35" in body, "the file must show the same figure as the screen"
    # A missing value reads the same in the file as on the page, rather than
    # as an empty cell that could be mistaken for a zero.
    assert db.BLANK in body

    resp = exports.csv_response("coverage_MCV1_2015", columns, rows)
    assert "charset=utf-8" in resp.headers["Content-Type"]
    disposition = resp.headers["Content-Disposition"]
    assert 'filename="coverage_MCV1_2015.csv"' in disposition
    assert "filename*=UTF-8''" in disposition, "needed for non-ASCII filenames"

    # A key the query does not return must read as no data, not raise: a typo
    # in a COLUMNS table should never 500 someone's download.
    odd = exports.csv_response("x", [("Missing", "nope", str)], rows)
    assert odd.status_code == 200


def check_export_dispatch():
    columns = [("Country", "country_name", str)]
    rows = [{"country_name": "Nauru"}]
    assert exports.send(None, "x", "t", "s", columns, rows) is None, \
        "an ordinary page view must not be treated as a download"
    assert exports.send("html", "x", "t", "s", columns, rows) is None
    assert exports.send("csv", "x", "t", "s", columns, rows).status_code == 200

    resp = exports.send("pdf", "x", "t", "s", columns, rows)
    if exports.pdf_available():
        assert resp.status_code == 200 and resp.data[:5] == b"%PDF-"
    else:
        # Without fpdf2 the PDF route explains itself instead of raising, and
        # everything else on the site keeps working.
        assert resp.status_code == 503 and b"fpdf2" in resp.data


def check_page_window():
    # Short lists are shown whole: an ellipsis standing in for one missing
    # number is wider than the number it hides.
    assert db.page_window(1, 1) == [1]
    assert db.page_window(1, 3) == [1, 2, 3]
    assert db.page_window(3, 5) == [1, 2, 3, 4, 5]

    # Long lists keep both ends reachable in one click.
    assert db.page_window(1, 27) == [1, 2, 3, None, 27]
    assert db.page_window(14, 27) == [1, None, 12, 13, 14, 15, 16, None, 27]
    assert db.page_window(27, 27) == [1, None, 25, 26, 27]

    # The properties that matter whatever the numbers: the reader can always
    # reach the first and last page, is always shown where they are, and never
    # sees the same page offered twice or out of order.
    for total in (1, 2, 5, 9, 27, 208):
        # paginate() clamps into range, so only in-range pages can ever reach
        # page_window -- feeding it an impossible page would test nothing real.
        for current in {1, 2, total // 2, total - 1, total} & set(range(1, total + 1)):
            window = db.page_window(current, total)
            numbers = [n for n in window if n is not None]
            assert numbers[0] == 1 and numbers[-1] == total, (current, total)
            assert current in numbers, (current, total)
            assert numbers == sorted(set(numbers)), (current, total)
            # A gap marker only ever stands for a real gap.
            for i, n in enumerate(window):
                if n is None:
                    assert window[i + 1] - window[i - 1] > 2, (current, total)

    # Every page paginate() can hand back must be offerable by the window.
    page = db.paginate(list(range(100)), 4, 8)
    assert page["window"] == db.page_window(page["page"], page["pages"])


if __name__ == "__main__":
    checks = [check_paginate, check_validate, check_fmt_num,
              check_page_window, check_csv, check_export_dispatch]
    for check in checks:
        check()
        print("PASS  %s" % check.__name__)
    print("\n%d / %d checks passed." % (len(checks), len(checks)))
