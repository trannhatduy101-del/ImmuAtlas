# ImmuAtlas

Investigating preventable infectious diseases, built on WHO immunization
data. Flask app backed by SQLite; no JavaScript framework, no build step.

## Prerequisites

- Python 3.10+
- Bash to run `rebuild_db.sh` (Git Bash, WSL, or any Unix shell). No
  `sqlite3` CLI required — the script falls back to Python's `sqlite3`
  module if it isn't installed.

## Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

./rebuild_db.sh        # builds immuatlas.db from immunisation2.db + sql/
flask --app app run --debug
```

Then open http://127.0.0.1:5000.

`immuatlas.db` is git-ignored and disposable — it's rebuilt from the
committed `immunisation2.db` (read-only source data) and the schema/seed
scripts in `sql/`. Run `./rebuild_db.sh` again any time `sql/` changes.

## Verifying the data layer

```bash
python verify.py
```

Checks the database against a set of known figures (row counts, averages,
etc.) and fails loudly if the schema or seed produces a different number.
Run it after every `rebuild_db.sh`.

## Project layout

```
app.py          application factory, blueprint registration, error pages
config.py       paths and site constants
db.py           all SQLite access: connect/query helpers, named-query
                loader, safe ORDER BY whitelist, display formatters
routes/         one module per page (see table below)
queries/        one .sql file per named query, loaded by db.load_query()
sql/            schema, seed, and provenance scripts used by rebuild_db.sh
templates/      Jinja templates (base layout + one file per page)
static/         CSS and images
verify.py       data-integrity checks against expected figures
rebuild_db.sh   rebuilds immuatlas.db from immunisation2.db + sql/
```

## Pages

| Route             | Page                          | Status      |
|-------------------|-------------------------------|-------------|
| `/`                | Landing                       | Built       |
| `/mission`         | Mission statement             | Placeholder |
| `/coverage`        | Vaccination rates             | Built       |
| `/infections`      | Infections by economic status | Placeholder |
| `/improvement`     | Biggest improvement           | Placeholder |
| `/above-average`   | Countries above the global rate | Placeholder |

Placeholder pages render an "unbuilt" component rather than erroring, so
the full nav and footer work even before every page is implemented.

## Notes

- Every value from a request is bound as a SQL parameter; the only
  exception is `ORDER BY`, which is resolved through a fixed whitelist per
  route (`db.safe_order_by`) since column names can't be bound.
- Pages query views (`v_coverage`, `v_infection`, ...), never the raw
  `Vaccination` / `InfectionData` tables — those store missing values as
  empty strings rather than `NULL`, which silently corrupts aggregates.
