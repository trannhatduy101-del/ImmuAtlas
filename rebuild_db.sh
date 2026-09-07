#!/usr/bin/env bash
#
# Rebuild the working database from the committed original.
#
#   immunisation2.db  supplied source data. READ ONLY. Never modified.
#   immuatlas.db      working copy. Disposable, gitignored, rebuilt by this script.
#   sql/              our own schema, seed and provenance layers.
#
# Run from the project root:  ./rebuild_db.sh
#
set -euo pipefail

cd "$(dirname "$0")"

SOURCE="immunisation2.db"
WORKING="immuatlas.db"

SQL_FILES="sql/schema_immuatlas.sql sql/seed_immuatlas.sql sql/data_source_who.sql"

# ---------------------------------------------------------------------------
# How to talk to SQLite.
#
# The sqlite3 command line tool is the obvious choice, but it is not installed
# by default on Windows and is not part of Git Bash. Python's sqlite3 module is
# in the standard library and drives the same engine, so the script falls back
# to it rather than stopping. Either path produces an identical database.
# ---------------------------------------------------------------------------
PY=""
if command -v sqlite3 >/dev/null 2>&1; then
    MODE="cli"
elif command -v python3 >/dev/null 2>&1 && python3 -c "import sqlite3" >/dev/null 2>&1; then
    MODE="python"; PY="python3"
elif command -v python >/dev/null 2>&1 && python -c "import sqlite3" >/dev/null 2>&1; then
    MODE="python"; PY="python"
else
    echo "error: needs either the sqlite3 command line tool or Python 3." >&2
    echo "       Install one of them, then run this again." >&2
    exit 1
fi

run_sql () {
    if [ "$MODE" = "cli" ]; then
        sqlite3 "$WORKING" < "$1"
    else
        "$PY" - "$WORKING" "$1" <<'PYEOF'
import sqlite3, sys
target, script = sys.argv[1], sys.argv[2]
conn = sqlite3.connect(target)
with open(script, encoding="utf-8") as handle:
    conn.executescript(handle.read())
conn.commit()
conn.close()
PYEOF
    fi
}

for f in "$SOURCE" $SQL_FILES; do
    [ -f "$f" ] || { echo "error: missing required file: $f" >&2; exit 1; }
done

# Fingerprint the source so we can prove we never touched it.
checksum() {
    if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
    else shasum -a 256 "$1" | cut -d' ' -f1
    fi
}
before="$(checksum "$SOURCE")"

rm -f "$WORKING"
cp "$SOURCE" "$WORKING"
for f in $SQL_FILES; do
    run_sql "$f"
done

after="$(checksum "$SOURCE")"
if [ "$before" != "$after" ]; then
    echo "error: $SOURCE was modified during the rebuild. This must never happen." >&2
    exit 1
fi

echo "Rebuilt $WORKING from $SOURCE using the $MODE path. Source unchanged."
