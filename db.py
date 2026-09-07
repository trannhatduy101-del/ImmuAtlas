"""
Database access layer for ImmuAtlas.

Everything that touches SQLite goes through here. Three rules from CLAUDE.md
section 7 hold everywhere in this file, and they are the whole reason it exists:

  1. Query the views, never raw Vaccination or InfectionData. Those tables store
     missing values as empty strings, not NULL, and SQLite sorts TEXT above every
     number, so AVG(coverage) silently reads 68.52 where the truth is 88.26. See
     CLAUDE.md 4.1. Nothing in this module hides that; it is the caller's job to
     name a view.

  2. Every value from a request is a bound parameter. No f-strings, no .format(),
     no concatenation inside any SQL string here or in queries/.

  3. A column name cannot be a bound parameter. SQLite will not accept
     "ORDER BY ?" as a column reference, so a user-chosen sort is resolved
     against a fixed whitelist before it reaches the SQL. safe_order_by() is
     that whitelist, and it is the only place a name is ever interpolated.

Rebuild the working database with ./rebuild_db.sh after changing sql/.
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
            "No database at %s. Run ./rebuild_db.sh to build it." % target
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


def scalar(sql, params=()):
    """Return the first column of the first row, or None if there are no rows.

    For COUNT(*), AVG(), MAX() and friends, where one number is the answer.
    """
    row = query_one(sql, params)
    return None if row is None else row[0]


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
    neutralising the unused ones (CLAUDE.md section 3):

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


# ---------------------------------------------------------------------------
# Display formatting
#
# Presentation only (CLAUDE.md section 7, "Python versus SQL"). These return
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

    CLAUDE.md 8.1A wants the landing facts read as '10.62 billion doses', so
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

    Values above 100 are kept, not capped: CLAUDE.md 4.5 records 1,312 such
    rows with a maximum of 169.35, and doses given outside the target cohort
    are real.
    """
    try:
        return "%.*f%%" % (digits, float(value))
    except (TypeError, ValueError):
        return BLANK
