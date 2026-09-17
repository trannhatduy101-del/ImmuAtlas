"""
Database access layer for ImmuAtlas.

Everything that touches SQLite goes through here. Three rules from the project spec
section 7 hold everywhere in this file, and they are the whole reason it exists:

  1. Query the views, never raw Vaccination or InfectionData. Those tables store
     missing values as empty strings, not NULL, and SQLite sorts TEXT above every
     number, so AVG(coverage) silently reads 68.52 where the truth is 88.26. See
     the project spec 4.1. Nothing in this module hides that; it is the caller's job to
     name a view.

  2. Every value from a request is a bound parameter. No f-strings, no .format(),
     no concatenation inside any SQL string here or in queries/.

  3. A column name cannot be a bound parameter. SQLite will not accept
     "ORDER BY ?" as a column reference, so a user-chosen sort is resolved
     against a fixed whitelist before it reaches the SQL. safe_order_by() is
     that whitelist, and it is the only place a name is ever interpolated.

Rebuild the working database with `python rebuild_db.py` after changing sql/.
"""

import os
import re
import sqlite3

import config

DB_PATH = config.DB_PATH


class DatabaseMissing(RuntimeError):
    """Raised when the working database has not been built yet."""


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def connect(path=None):
    """Open a connection to the working database.

    Rows come back as sqlite3.Row, so a row behaves like a tuple AND like a
    dict: row[0], row["coverage_reported"] and dict(row) all work. Templates
    read far better with names than with positional indexes.

    Each call returns a fresh connection. SQLite connections are not safe to
    share across threads, and a local file is cheap to open, so per-query
    connections are the simple correct choice here rather than a pool we would
    have to make thread-safe.
    """
    target = path or DB_PATH
    if not os.path.exists(target):
        raise DatabaseMissing(
            "No database at %s. Run: python rebuild_db.py" % target
        )
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Query helpers
#
# params is always a sequence or dict of BOUND values. sqlite3 escapes them.
# Passing user input here is safe; splicing user input into `sql` is not.
# ---------------------------------------------------------------------------

def query(sql, params=()):
    """Run a SELECT and return all rows as a list of sqlite3.Row."""
    conn = connect()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def query_one(sql, params=()):
    """Run a SELECT and return the first row, or None if there are no rows."""
    conn = connect()
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Named queries
# ---------------------------------------------------------------------------

_QUERY_CACHE = {}
_QUERY_NAME = re.compile(r"^[a-z0-9_]+$")


def load_query(name):
    """Return the SQL text of queries/<name>.sql, cached after the first read.

    Named queries live in their own files so the SQL stays reviewable and can be
    pointed at during the presentation, which is what Level 3 is marked on.

    Because a query lives in a static file it cannot assemble its own WHERE
    clause. Handle an optional filter by making every filter always present and
    neutralising the unused ones (the project spec section 3):

        WHERE (:antigen IS NULL OR antigen    = :antigen)
          AND (:year    IS NULL OR year       = :year)
          AND (:country IS NULL OR country_id = :country)

    then pass None for whatever the user left blank. One query, all states.

    `name` is a developer-chosen identifier, never a request value, but it is
    validated anyway: a name that could contain a path separator or '..' would
    turn this helper into an arbitrary file read.
    """
    if not _QUERY_NAME.match(name or ""):
        raise ValueError("bad query name %r: use lowercase, digits and _" % name)
    if name not in _QUERY_CACHE:
        path = os.path.join(config.QUERIES_DIR, name + ".sql")
        with open(path, encoding="utf-8") as handle:
            _QUERY_CACHE[name] = handle.read()
    return _QUERY_CACHE[name]


# ---------------------------------------------------------------------------
# Safe sorting
# ---------------------------------------------------------------------------

def safe_order_by(requested, allowed, default):
    """Resolve a user-supplied sort key to a trusted SQL fragment.

    `allowed` maps a user-facing key to a fixed SQL fragment that WE wrote:

        ORDER_KEYS = {
            "rate":    "cases_per_100k DESC",
            "country": "country_name ASC",
        }
        frag = safe_order_by(request.args.get("sort"), ORDER_KEYS, "rate")
        rows = query(load_query("coverage_by_country") + " ORDER BY " + frag, params)

    That concatenation is safe, and it is the only concatenation allowed
    anywhere near SQL in this project, because `frag` can only ever be one of
    the literal strings in ORDER_KEYS. Nothing the user typed survives: an
    unknown, missing or hostile key returns the default fragment. So
    safe_order_by("; DROP TABLE x", {"rate": "cases_per_100k"}, "rate")
    returns "cases_per_100k" -- the input is discarded, not escaped and
    passed through.

    A bound parameter cannot do this job. "ORDER BY ?" binds a *value*, so
    SQLite sorts every row by the same constant and the sort silently does
    nothing. The whitelist is not extra caution on top of binding; for an
    identifier it is the only mechanism that exists.

    Raises ValueError if `default` is not itself in `allowed`, because that is
    a bug in our code and should be loud, not a silently unsorted table.
    """
    if default not in allowed:
        raise ValueError(
            "default sort key %r is not in the allowed map %r"
            % (default, sorted(allowed))
        )
    if isinstance(requested, str) and requested in allowed:
        return allowed[requested]
    return allowed[default]


def validate(raw, allowed, cast=str):
    """Resolve a request value against the set of values we actually offer.

    Returns (value, rejected). This is the safety boundary the project spec
    puts in Python: a value that is not on the list never reaches the database.

    Dropping an unrecognised filter WIDENS the selection, so the fact that it
    was dropped is returned too and the page says so. Silently ignoring a
    filter is how someone reads a figure for "all years" believing they asked
    for one year.

    An absent or empty value is not an error -- it means "no filter" -- so it
    returns (None, False), while a value that is present but not on the list
    returns (None, True).
    """
    if raw is None or raw == "":
        return None, False
    try:
        value = cast(raw)
    except (TypeError, ValueError):
        return None, True
    if value in allowed:
        return value, False
    return None, True


# ---------------------------------------------------------------------------
# Pagination
#
# Slicing an ALREADY-SORTED list is not sorting and not aggregating, so it does
# not cross the SQL/Python line the project spec draws: SQL decided the order
# and the membership, this only decides which slice is on screen.
# ---------------------------------------------------------------------------

PAGE_SIZES = (8, 15, 25, 50)
DEFAULT_PAGE_SIZE = 8


def page_window(page, pages, span=2):
    """Page numbers to offer as links, with None where numbers were skipped.

        page_window(14, 27) -> [1, None, 12, 13, 14, 15, 16, None, 27]

    Twenty-seven numbered links is a wall, and hiding the first and last leaves
    no way to reach either end in one click. So: always both ends, `span` on
    each side of where the reader is, and a None wherever a run was cut -- the
    template draws that as an ellipsis, not as a link to nowhere.

    A None is only inserted for a real gap. With pages=5 the window already
    covers everything, and an ellipsis standing in for a single missing number
    is wider than the number it replaces.
    """
    wanted = {1, pages}
    wanted.update(range(max(1, page - span), min(pages, page + span) + 1))

    out = []
    previous = 0
    for n in sorted(wanted):
        skipped = n - previous - 1
        if skipped == 1:
            # Exactly one number missing: print it. An ellipsis is wider than
            # the digit it would hide, and it costs the reader a click.
            out.append(n - 1)
        elif skipped > 1:
            out.append(None)
        out.append(n)
        previous = n
    return out


def paginate(rows, page_raw, size_raw=None, sizes=PAGE_SIZES,
             default_size=DEFAULT_PAGE_SIZE):
    """Cut one page out of a list of rows for display.

    A bad PAGE number is clamped into range rather than 404'd: asking for page
    999 of a 3-page table is a stale bookmark, not an error, and clamping never
    widens a selection. A bad page SIZE falls back to the default. Either one
    sets `rejected` so the page can tell the reader a control was ignored.

    Returns a dict rather than a tuple because the template reads it by name
    (page.rows, page.total, ...) and a 9-tuple at the call site is unreadable.
    """
    # ponytail: whole result set held in memory and sliced here. The largest
    # table in this dataset is ~212 rows; move to SQL LIMIT/OFFSET past ~5k.
    size, rejected = validate(size_raw, set(sizes), int)
    if size is None:
        size = default_size

    total = len(rows)
    pages = max(1, -(-total // size))       # ceiling division

    page = 1
    if page_raw not in (None, ""):
        try:
            page = int(page_raw)
        except (TypeError, ValueError):
            rejected = True
    page = max(1, min(page, pages))

    start = (page - 1) * size
    return {
        "rows": rows[start:start + size],
        "page": page,
        "pages": pages,
        "size": size,
        "sizes": list(sizes),
        "total": total,
        "window": page_window(page, pages),
        "first": start + 1 if total else 0,
        "last": min(start + size, total),
        "rejected": rejected,
    }


# ---------------------------------------------------------------------------
# Display formatting
#
# Presentation only (the project spec section 7, "Python versus SQL"). These return
# strings and must never be used to build a value that goes back into a query.
# ---------------------------------------------------------------------------

BLANK = "no data"


def fmt_int(value):
    """24211 -> '24,211'. None or non-numeric -> 'no data'."""
    try:
        return "{:,}".format(int(round(float(value))))
    except (TypeError, ValueError):
        return BLANK


def fmt_big(value):
    """Compact magnitude for stat cards: 10620000000 -> '10.62 billion'.

    the project spec 8.1A wants the landing facts read as '10.62 billion doses', so
    this spells the scale word out rather than abbreviating to '10.6B'. Use
    fmt_int wherever the exact figure matters; this one trades digits for
    readability, so never use it for a number a reader has to verify.
    """
    try:
        n = float(value)
    except (TypeError, ValueError):
        return BLANK
    sign = "-" if n < 0 else ""
    n = abs(n)
    for limit, word in ((1e12, "trillion"), (1e9, "billion"), (1e6, "million")):
        if n >= limit:
            return "%s%.2f %s" % (sign, n / limit, word)
    return sign + fmt_int(n)


def fmt_pct(value, digits=1):
    """88.256 -> '88.3%'. Expects a number already on a 0-100 scale, not 0-1.

    Coverage columns in this dataset are stored as percentages, so nothing is
    rescaled here. Rescaling silently is a good way to publish a chart that is
    wrong by a factor of a hundred.

    Values above 100 are kept, not capped: the project spec 4.5 records 1,312 such
    rows with a maximum of 169.35, and doses given outside the target cohort
    are real.
    """
    try:
        return "%.*f%%" % (digits, float(value))
    except (TypeError, ValueError):
        return BLANK


def fmt_num(value, digits=2):
    """12.3456 -> '12.35'. None or non-numeric -> 'no data'.

    Deliberately WITHOUT a thousands separator, unlike fmt_int. This is the
    formatter the exports share with the screen, and "1,234.5" lands in a
    spreadsheet as text, which defeats the point of exporting a number. The
    screen keeps fmt_int where grouping helps a reader; a cell that has to be
    summed uses this.
    """
    try:
        return "%.*f" % (digits, float(value))
    except (TypeError, ValueError):
        return BLANK
