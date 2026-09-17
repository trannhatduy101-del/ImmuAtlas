-- 2A: the country table.
--
-- Reads v_coverage. It used to read v_herd_immunity for the per-disease WHO
-- threshold, but this page now measures every antigen against one bar passed in
-- as :met_threshold, so that join produced three columns the page discarded.
-- All four of 2A's queries read the same view.
--
-- NOTE: this file deliberately does NOT end in a semicolon and carries no
-- ORDER BY. The sort is appended by the route from a fixed whitelist, because
-- a column name cannot be a bound parameter: "ORDER BY ?" binds a value, and
-- SQLite then sorts every row by the same constant and the sort silently does
-- nothing. See db.safe_order_by.
--
-- Every filter is always present and the unused ones are neutralised by
-- passing NULL, which is how one static file serves all four combinations of
-- country and region, including the combination that matches nothing.
SELECT
    country_id,
    country_name,
    COALESCE(region_name, 'Not classified')  AS region_name,
    year,
    antigen,
    antigen_name,
    disease_name,
    coverage_reported,
    -- What the table prints. The brief's own example tops out at 100
    -- ("Switzerland 100"), so the column is capped there; coverage_reported
    -- stays beside it, uncapped, for the flag on the row and for the download.
    -- Capped HERE and not in db.fmt_pct, because 1A, 2B and 3A's banner all
    -- still print the figure as reported.
    MIN(coverage_reported, 100)                  AS coverage_display,
    -- Bar geometry, on a 90-100 scale rather than 0-100. Every row in this
    -- table is at or above the threshold by definition, so a bar drawn from
    -- zero is between 90% and 100% full on every single row and the column
    -- shows nothing. Measured from the threshold, 90.4 and 99.8 are visibly
    -- different. The header says what the bar spans, because a bar that does
    -- not start at zero and does not say so is a lie by drawing.
    ROUND((MIN(coverage_reported, 100) - :met_threshold)
          * 100.0 / (100 - :met_threshold), 1)   AS bar_pct,
    doses_per_100_population,
    target_cohort,
    -- The two numbers the percentage is made of. On the row as a tooltip, so
    -- "why is this one 100%" is answerable without leaving the table.
    doses
FROM v_coverage
WHERE (:antigen IS NULL OR antigen    = :antigen)
  AND (:year    IS NULL OR year       = :year)
  AND (:country IS NULL OR country_id = :country)
  AND (:region  IS NULL OR region_id  = :region)
  -- Brief 2A, Table 1: "all countries that have MET at least 90% of their
  -- vaccination targets". One bar for every antigen, bound as :met_threshold
  -- rather than read from the row, because the brief names a single figure.
  -- WHO's own per-disease targets live in herd_immunity_threshold and are
  -- cited in the method note; nothing here is filtered or counted with them.
  -- Not optional: the brief asks for the countries that MET the target, so this
  -- table is only ever those. coverage_reported >= NULL is NULL, so a country
  -- that reported nothing falls out on its own -- "no figure" is not "met".
  AND coverage_reported >= :met_threshold
  -- Nine territories report vaccination figures but have no row in Country, so
  -- they have no name and no region -- two of the five columns the brief asks
  -- for. They are not dropped from the site: the regional table below still
  -- counts them on its "Not classified" row, and the note under this table says
  -- where they went.
  AND country_name IS NOT NULL
  -- The table's search box. Bound, never spliced, so a reader typing % or _ is
  -- searching for those characters rather than writing a pattern of their own.
  -- SQLite's LIKE is case-insensitive for ASCII, so "viet" finds "Viet Nam"
  -- without lowering either side.
  AND (:q IS NULL OR country_name LIKE '%' || :q || '%')
