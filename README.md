# ImmuAtlas

ImmuAtlas is a web application for investigating preventable infectious
diseases, built on immunisation data published by the World Health
Organization. It presents the same dataset at three levels of depth across
six pages, so that a reader can begin with a summary of global coverage and
end with a ranked comparison of individual countries over a period they
choose themselves.

The application is written in Python using Flask, and stores its data in
SQLite. It has no JavaScript at all, no front end framework and no build
step. Every control on every page is an ordinary HTML form or link, which
means the application runs offline, every result is reachable by its own
URL, and the browser back button behaves as a reader expects.

## Prerequisites

Python 3.10 or later. No other software is required.

## Setup

Create a virtual environment and install the two dependencies.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS and Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Running the application

```bash
python run.py
```

Open http://127.0.0.1:5000 in a browser. That is the entire setup. On the
first start the application notices that no working database exists and
builds one, which takes a few seconds. Every start after that is
immediate.

To run the auto reloading development server instead:

```bash
flask --app run run --debug
```

## Rebuilding the working database

The file `immuatlas.db` is a copy of the supplied, read only
`immunisation2.db` with this project's schema, views and seed data applied
on top of it. It is deliberately excluded from version control, because it
is a generated binary and the state that matters lives in the SQL scripts
under `src/sql/`.

The application builds this file for you whenever it is missing, so the
command below is only needed after you have edited one of those scripts and
want the change applied immediately.

```bash
python src/rebuild_db.py
```

The rebuild applies three scripts in a fixed order, because each one depends
on the one before it. First `src/sql/schema_immuatlas.sql` creates the
project tables and views. Then `src/sql/seed_immuatlas.sql` loads the team
members, the personas and the research sources. Finally
`src/sql/data_source_who.sql` records the provenance shown in the site
footer. The work is done through Python's own `sqlite3` module, so no
command line SQLite tool is needed and the same command works on Windows,
macOS and Linux.

The rebuild writes to a temporary file and moves it into place only once
every step has succeeded. A failed rebuild therefore leaves the previous
working database untouched rather than replacing it with a half built one.

The script also reports the two foreign key anomalies present in the
supplied data, namely that Ethiopia and Venezuela carry no economic
classification. These rows are kept exactly as supplied. The views resolve
them to the label `Not classified` rather than dropping the two countries
from the dataset.

If the automatic build cannot run at all, because `immunisation2.db` is
absent or the directory cannot be written to, the application still starts
and every page returns a 503 response explaining the problem, rather than
failing with a traceback.

## Project layout

```
run.py             the only entry point. It puts src/ on sys.path and starts Flask
immunisation2.db   the supplied WHO data, read only and never modified. It is the
                   one file here that cannot be regenerated
README.md          this file
requirements.txt   Flask, and fpdf2 for the PDF export

src/               the application
  app.py           application factory, blueprint registration, error pages,
                   and the first run database build
  config.py        paths and site wide constants
  db.py            all SQLite access. Connection and query helpers, the named
                   query loader, the ORDER BY whitelist, pagination and the
                   value formatters
  exports.py       CSV and PDF for every result table, with the columns of each
                   table declared once and shared by both formats
  rebuild_db.py    rebuilds immuatlas.db from immunisation2.db and src/sql/
  test_helpers.py  assert based checks for db.py and exports.py. No test
                   framework is used. Run it with python src/test_helpers.py
  worldmap.py      generated country outlines for the globe on page 3A. Rebuild
                   it with python tools/build_worldmap.py
  routes/          one module per page
  queries/         one .sql file per named query, loaded by db.load_query() by
                   file name alone. The folders mirror routes/ and are named
                   shell, filter, landing, mission, coverage, infections,
                   improvement and above_average
  sql/             schema, seed and provenance scripts, applied in that order
  templates/       base.html, the macros in _controls.html that every result
                   table shares, and one file per page under pages/
  static/          stylesheets, self hosted fonts and images

tools/             one off scripts, never imported by the application
  build_worldmap.py downloads the Natural Earth country outlines, which are in
                   the public domain, and projects them for the globe on 3A
  make_hero_image.py resizes and blurs the hero background photograph on page 1A
                   and writes it out as WebP
  recolour.py      rotates every colour in the stylesheets from one hue to
                   another in the OKLCH colour space, keeping lightness and
                   chroma unchanged so that the measured contrast ratios
                   survive the change. It produced the current green palette
```

## Pages

| Route            | Page                            | Level | Sub-task |
|------------------|---------------------------------|-------|----------|
| `/`              | Landing                         | 1     | A        |
| `/mission`       | Mission statement               | 1     | B        |
| `/coverage`      | Vaccination rates               | 2     | A        |
| `/infections`    | Infections by economic status   | 2     | B        |
| `/improvement`   | Biggest improvement             | 3     | A        |
| `/above-average` | Countries above the global rate | 3     | B        |

## Exporting a result

Every result table can be downloaded as CSV or as PDF from the buttons in
its header. A download always contains the whole filtered result rather
than the page currently on screen, so a reader who has narrowed a selection
receives all of it and not merely the first ten rows.

The CSV carries a UTF-8 byte order mark, which is what allows a spreadsheet
application to render names such as Côte d'Ivoire correctly. Missing values
are written as the words `no data` in the file, exactly as they appear on
the page, so that a blank cell never has to be interpreted.

The PDF export requires the `fpdf2` package, which is listed in
`requirements.txt`. If that package is absent the site and the CSV export
continue to work, and the PDF link is simply not shown.

## Technical decisions

Every value that arrives from a request is bound as a SQL parameter. The
single exception is the `ORDER BY` clause, because a column name cannot be
bound as a value. Each route therefore resolves the requested sort through a
fixed whitelist of permitted clauses, implemented in `db.safe_order_by`.
A sort key that is not on the list falls back to the default and the page
states that part of the request was ignored.

Every sort offered by a page orders a column that the page actually
displays. A control that reorders rows by a figure the reader cannot see
produces an order that looks arbitrary, so such options were removed.

Pages read from views such as `v_coverage` and `v_infection` rather than
from the raw `Vaccination` and `InfectionData` tables. The supplied tables
record a missing value as an empty string rather than as NULL, which
silently corrupts any aggregate computed over them. The views correct this
in one place so that no page has to remember it.

The personas on the mission page and the names and student numbers of the
team are read from the database on every request, never written into a
template or a Python constant, as the project specification requires.

The globe on page 3A is drawn from country outlines published by Natural
Earth, specifically the 1:110m Admin 0 Countries set, which is in the public
domain. The outlines are projected once by `tools/build_worldmap.py` and
stored as a generated Python module, so the running application never
fetches anything from the network.

The hero of page 1A uses a single background photograph, prepared by
`tools/make_hero_image.py`. That script resizes the image and applies a
Gaussian blur before writing it out, because the photograph carries legible
text of its own that would otherwise sit behind the hero headline. Blurred, it
contributes texture and nothing else. A green gradient is laid over it at
partial opacity so that the image cannot pull the page away from its palette,
and the same gradient is repeated underneath at full opacity, so that a hero
whose image has not yet loaded still presents white text on a dark green band
rather than on white. Every other graphic on the page remains hand-drawn SVG.

Filtering, sorting, joining and aggregation are all performed in SQL.
Python validates the incoming request, whitelists the sort column, converts
figures into the geometry a chart needs, and formats values for display.
Nothing is sorted or aggregated in Python.

## How anomalies in the data are handled

The specification requires that anomalies be identified and handled rather
than hidden, so each one is dealt with visibly.

Some countries report coverage above 100 per cent, because they delivered
more doses than there were children in the target group they were measured
against. There are 1,312 such records, the highest being 169.35 per cent.
On the country table of page 2A the figure is shown as 100 per cent, which
matches the example given in the specification, and the row carries a small
label naming the figure that was actually reported. The downloaded file
keeps the reported figure unchanged. Page 3A does not cap anything, because
it measures the change between two years and capping would understate the
countries that improved the most.

Nine territories report vaccination figures but have no row in the country
table, and therefore have neither a name nor a region. They are left out of
the country table on page 2A, where two of the five required columns would
be empty for them, and a note under that table says where they went. They
remain counted on the `Not classified` row of the regional table above it,
which is labelled as not being a region.

Countries that reported no figure at all are excluded from averages rather
than counted as zero, since an absent measurement and a measurement of zero
are different statements. On page 2B, a country that reported exactly zero
cases in every year of the dataset is flagged in its own column, so that a
reader can see how many such records contribute to a total.
