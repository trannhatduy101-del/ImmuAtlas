# ImmuAtlas

Investigating preventable infectious diseases, built on WHO immunization
data. Flask app backed by SQLite; no JavaScript framework, no build step.

## Prerequisites

- Python 3.10+

## Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Build the working database

`immuatlas.db` is git-ignored and disposable: it is a copy of the supplied
`immunisation2.db` (read-only source data) with this project's schema,
views and seed data applied on top. Rebuild it any time `sql/` changes.

```bash
cp immunisation2.db immuatlas.db
sqlite3 immuatlas.db < sql/schema_immuatlas.sql
sqlite3 immuatlas.db < sql/seed_immuatlas.sql
sqlite3 immuatlas.db < sql/data_source_who.sql
```

The three scripts must run in that order, and each is safe to re-run.
Without the `sqlite3` CLI, Python's built-in module does the same job:

```bash
python -c "import sqlite3, shutil; shutil.copy('immunisation2.db', 'immuatlas.db'); c = sqlite3.connect('immuatlas.db'); [c.executescript(open(f, encoding='utf-8').read()) for f in ('sql/schema_immuatlas.sql', 'sql/seed_immuatlas.sql', 'sql/data_source_who.sql')]; c.commit()"
```

## Run

```bash
flask --app app run --debug
```

Then open http://127.0.0.1:5000.

## Project layout

```
app.py          application factory, blueprint registration, error pages
config.py       paths and site constants
db.py           all SQLite access: connect/query helpers, named-query
                loader, safe ORDER BY whitelist, display formatters
routes/         one module per page (see table below)
queries/        one .sql file per named query, loaded by db.load_query()
sql/            schema, seed, and provenance scripts
templates/      Jinja templates (base layout + one file per page)
static/         CSS, fonts and images
```

## Pages

| Route            | Page                            | Sub-task |
|------------------|---------------------------------|----------|
| `/`              | Landing                         | A        |
| `/mission`       | Mission statement               | B        |
| `/coverage`      | Vaccination rates               | A        |
| `/infections`    | Infections by economic status   | B        |
| `/improvement`   | Biggest improvement             | A        |
| `/above-average` | Countries above the global rate | B        |

## Notes

- Every value from a request is bound as a SQL parameter; the only
  exception is `ORDER BY`, which is resolved through a fixed whitelist per
  route (`db.safe_order_by`) since column names can't be bound.
- Pages query views (`v_coverage`, `v_infection`, ...), never the raw
  `Vaccination` / `InfectionData` tables — those store missing values as
  empty strings rather than `NULL`, which silently corrupts aggregates.
- Personas and team members are read from the database, never hardcoded in
  a template or a Python constant.
