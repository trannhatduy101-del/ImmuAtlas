"""
Rebuild the working database.

    python rebuild_db.py

immuatlas.db is a copy of the supplied read-only immunisation2.db with this
project's schema, views and seed data applied on top. It is git-ignored on
purpose: it is a generated SQLite binary, and the state that matters lives in
sql/. Run this after changing anything in sql/.

Order matters:
    1. sql/schema_immuatlas.sql  -> project tables and views
    2. sql/seed_immuatlas.sql    -> team, personas, research sources
    3. sql/data_source_who.sql   -> WHO provenance shown in the footer

The rebuild writes to a temporary file and only moves it into place once every
step has passed. A failed rebuild therefore leaves the previous working
database untouched, rather than replacing it with a half-built one.
"""

import os
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SOURCE_DB = ROOT / "immunisation2.db"
OUTPUT_DB = ROOT / "immuatlas.db"
TEMP_DB = ROOT / ".immuatlas.db.tmp"

# (label, path) in the order they must be applied.
SCRIPTS = [
    ("schema", ROOT / "sql" / "schema_immuatlas.sql"),
    ("seed", ROOT / "sql" / "seed_immuatlas.sql"),
    ("WHO provenance", ROOT / "sql" / "data_source_who.sql"),
]

# Objects the application will not start without. Checked after the scripts
# run, because executescript() reports a SQL error but not a script that
# succeeded while quietly creating nothing.
REQUIRED_OBJECTS = {
    "research_source",
    "user_group",
    "persona",
    "team_member",
    "data_source",
    "v_coverage",
    "v_infection",
}

# Printed at the end so the rebuild proves itself instead of just claiming
# success. A table that exists but is empty is a failed seed.
SANITY_CHECKS = [
    ("v_coverage rows", "SELECT COUNT(*) FROM v_coverage"),
    ("v_infection rows", "SELECT COUNT(*) FROM v_infection"),
    ("persona rows", "SELECT COUNT(*) FROM persona"),
    ("team members", "SELECT COUNT(*) FROM team_member"),
    ("WHO data sources", "SELECT COUNT(*) FROM data_source"),
]


def build(temp_db, scripts):
    """Apply every script to a fresh copy of the source database.

    Raises on the first problem. The caller removes the temporary file, so
    nothing half-built ever reaches immuatlas.db.

    Returns the rows PRAGMA foreign_key_check reported, for the caller to show.
    """
    shutil.copy2(SOURCE_DB, temp_db)

    conn = sqlite3.connect(temp_db)
    try:
        conn.execute("PRAGMA foreign_keys = ON")

        for label, path in scripts:
            print("Applying %s: %s" % (label, path.name))
            conn.executescript(path.read_text(encoding="utf-8"))

        placeholders = ",".join("?" for _ in REQUIRED_OBJECTS)
        found = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE name IN (%s)" % placeholders,
                tuple(REQUIRED_OBJECTS),
            )
        }
        missing = REQUIRED_OBJECTS - found
        if missing:
            raise RuntimeError(
                "the SQL ran but these objects were not created: "
                + ", ".join(sorted(missing))
            )

        # Reported, not fatal. The supplied immunisation2.db carries two of
        # these -- Ethiopia and Venezuela have economy = '' rather than NULL or
        # a real id, which is the empty-string-for-missing trap this whole
        # project is built around. v_coverage already resolves both to
        # 'Not classified', so the data IS handled; failing the rebuild over an
        # anomaly in read-only supplied data would mean nobody could build at
        # all. Printing them is the point: the shell script this replaced ran
        # the same PRAGMA and threw the result away, so it never once told
        # anyone they were there.
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()

        conn.commit()
        return violations
    finally:
        conn.close()


def report(db_path):
    conn = sqlite3.connect(db_path)
    try:
        print("\nDatabase created: %s" % db_path)
        for label, sql in SANITY_CHECKS:
            print("  %-18s %s" % (label + ":", conn.execute(sql).fetchone()[0]))
    finally:
        conn.close()


def main(argv=None):
    """Returns a process exit code: 0 on success, 1 on anything else."""
    missing = [p for p in [SOURCE_DB] + [p for _, p in SCRIPTS] if not p.is_file()]
    if missing:
        for path in missing:
            print("ERROR: required file not found: %s" % path, file=sys.stderr)
        return 1

    TEMP_DB.unlink(missing_ok=True)
    try:
        violations = build(TEMP_DB, SCRIPTS)
    except Exception as exc:
        # A readable line for whoever ran this, not a traceback. The previous
        # immuatlas.db is still in place because the move below never happened.
        print("ERROR: rebuild failed: %s" % exc, file=sys.stderr)
        TEMP_DB.unlink(missing_ok=True)
        return 1

    # Atomic on every platform this runs on, and unlike Path.rename it is
    # allowed to overwrite an existing file on Windows.
    os.replace(TEMP_DB, OUTPUT_DB)

    report(OUTPUT_DB)

    if violations:
        print("\nForeign key anomalies in the supplied data (%d), kept as supplied:"
              % len(violations))
        for table, rowid, parent, _fk in violations:
            print("  %s rowid %s has no matching %s row" % (table, rowid, parent))
        print("  The views resolve these to 'Not classified' rather than dropping them.")
    print("\nRebuilt immuatlas.db from immunisation2.db and sql/.")
    print("You can now run: python app.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
