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
python rebuild_db.py
```

It applies `sql/schema_immuatlas.sql`, `sql/seed_immuatlas.sql` and
`sql/data_source_who.sql` in that order — the order matters — using
Python's own `sqlite3` module, so no `sqlite3` command-line tool is
needed. The same command works on Windows, macOS and Linux.

The rebuild writes to a temporary file and only moves it into place once
every step has passed, so a failed rebuild leaves your previous
`immuatlas.db` untouched rather than replacing it with a half-built one.

It also reports the two foreign key anomalies in the supplied data
(Ethiopia and Venezuela have no economic classification). These are kept
as supplied; the views resolve them to `Not classified` rather than
dropping the countries.

Until the database exists, every page says so and returns 503 rather
than erroring, so a fresh clone tells you what to do instead of
crashing.

## Run

```bash
flask --app app run --debug
```

Then open http://127.0.0.1:5000.

## Project layout

```
app.py             application factory, blueprint registration, error pages
config.py          paths and site constants
db.py              all SQLite access: connect/query helpers, named-query
                   loader, safe ORDER BY whitelist, pagination, formatters
exports.py         CSV and PDF for every result table, columns declared once
rebuild_db.py      rebuilds immuatlas.db from immunisation2.db + sql/
test_helpers.py    assert-based checks for db.py and exports.py; no framework,
                   run it with: python test_helpers.py

routes/            one module per page (see the table below)
queries/           one .sql file per named query, loaded by db.load_query();
                   the name prefix says which page uses it (landing_, coverage_,
                   infections_, persona_, filter_)
sql/               schema, seed and provenance scripts, applied in that order
templates/         base.html, the _controls.html macros shared by every result
                   table, and one file per page under pages/
static/            CSS, self-hosted fonts and images

immunisation2.db   the supplied WHO data, read-only and never modified; the one
                   file here that cannot be regenerated
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

## Exports

Every result table exports the **whole filtered result**, not the page on
screen, as CSV or PDF. The CSV carries a UTF-8 byte-order mark so Excel
renders names like `Côte d'Ivoire` correctly, and missing values read
`no data` in the file exactly as they do on the page.

PDF export needs `fpdf2` (in `requirements.txt`). Without it the site and
the CSV export still work — the PDF link simply does not appear.

## Notes

- Every value from a request is bound as a SQL parameter; the only
  exception is `ORDER BY`, which is resolved through a fixed whitelist per
  route (`db.safe_order_by`) since column names can't be bound.
- Pages query views (`v_coverage`, `v_infection`, ...), never the raw
  `Vaccination` / `InfectionData` tables — those store missing values as
  empty strings rather than `NULL`, which silently corrupts aggregates.
- Personas and team members are read from the database, never hardcoded in
  a template or a Python constant.
