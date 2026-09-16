#!/usr/bin/env bash
set -euo pipefail

# =====================================================================
# ImmuAtlas - rebuild the working database
#
# Rebuilds immuatlas.db from the supplied read-only immunisation2.db and
# the SQL files committed in this repository.
#
# Order matters:
#   1. schema_immuatlas.sql  -> project tables + views
#   2. seed_immuatlas.sql    -> team, personas, research data, etc.
#   3. data_source_who.sql   -> WHO data provenance used by the footer
#
# immuatlas.db is intentionally git-ignored because it is a generated
# SQLite binary. Running this script recreates it from version-controlled
# source files.
# =====================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DB="$ROOT_DIR/immunisation2.db"
OUTPUT_DB="$ROOT_DIR/immuatlas.db"
TEMP_DB="$ROOT_DIR/.immuatlas.db.tmp"
SCHEMA_SQL="$ROOT_DIR/sql/schema_immuatlas.sql"
SEED_SQL="$ROOT_DIR/sql/seed_immuatlas.sql"
SOURCE_SQL="$ROOT_DIR/sql/data_source_who.sql"

# Prefer python3, but Windows Git Bash commonly exposes the command as python.
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "ERROR: Python was not found on PATH."
    exit 1
fi

for file in "$SOURCE_DB" "$SCHEMA_SQL" "$SEED_SQL" "$SOURCE_SQL"; do
    if [[ ! -f "$file" ]]; then
        echo "ERROR: Required file not found: $file"
        exit 1
    fi
done

rm -f "$TEMP_DB"

# Use Python's built-in sqlite3 module rather than relying on the sqlite3
# command-line program being installed. This works with the project's
# existing Python environment on Windows, macOS and Linux.
"$PYTHON_BIN" - "$SOURCE_DB" "$TEMP_DB" "$SCHEMA_SQL" "$SEED_SQL" "$SOURCE_SQL" <<'PY'
import os
import shutil
import sqlite3
import sys

source_db, temp_db, schema_sql, seed_sql, provenance_sql = sys.argv[1:]

shutil.copy2(source_db, temp_db)

try:
    conn = sqlite3.connect(temp_db)
    conn.execute("PRAGMA foreign_keys = ON")

    for label, path in (
        ("schema", schema_sql),
        ("seed", seed_sql),
        ("WHO provenance", provenance_sql),
    ):
        print(f"Applying {label}: {os.path.basename(path)}")
        with open(path, "r", encoding="utf-8") as handle:
            conn.executescript(handle.read())

    # Confirm the objects that the application depends on were created.
    required = {
        "research_source",
        "user_group",
        "persona",
        "team_member",
        "data_source",
        "v_coverage",
        "v_infection",
    }
    rows = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE name IN (%s)" % ",".join("?" for _ in required),
        tuple(required),
    ).fetchall()
    found = {row[0] for row in rows}
    missing = required - found
    if missing:
        raise RuntimeError(
            "Rebuild completed SQL execution but required objects are missing: "
            + ", ".join(sorted(missing))
        )

    conn.execute("PRAGMA foreign_key_check")
    conn.commit()
    conn.close()
except Exception:
    try:
        conn.close()
    except Exception:
        pass
    if os.path.exists(temp_db):
        os.remove(temp_db)
    raise
PY

mv -f "$TEMP_DB" "$OUTPUT_DB"

# Quick application-level sanity checks.
"$PYTHON_BIN" - "$OUTPUT_DB" <<'PY'
import sqlite3
import sys

db_path = sys.argv[1]
conn = sqlite3.connect(db_path)
checks = {
    "v_coverage rows": "SELECT COUNT(*) FROM v_coverage",
    "persona rows": "SELECT COUNT(*) FROM persona",
    "team members": "SELECT COUNT(*) FROM team_member",
    "WHO data sources": "SELECT COUNT(*) FROM data_source",
    "v_infection rows": "SELECT COUNT(*) FROM v_infection",
}

print("Database created:", db_path)
for label, sql in checks.items():
    print(f"  {label}: {conn.execute(sql).fetchone()[0]}")

conn.close()
PY

echo ""
echo "Rebuilt immuatlas.db successfully from immunisation2.db and sql/."
echo "You can now run: python app.py" 
