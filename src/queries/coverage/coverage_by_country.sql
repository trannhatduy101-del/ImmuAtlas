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
    COALESCE(country_name, country_id)  AS country_name,
    COALESCE(region_name, 'Not classified')  AS region_name,
    year,
    antigen,
    antigen_name,
    disease_name,
    coverage_reported,
    doses_per_100_population,
    target_cohort,
    -- How far above the bar, measured against the same :met_threshold the WHERE
    -- clause filters on, so the number and the filter can never disagree. A
    -- status column sat here too; now that the table is only ever the countries
    -- that met the target, it said "At or above target" on every single row.
    ROUND(coverage_reported - :met_threshold, 2) AS gap_to_threshold,
    CASE WHEN country_name IS NULL THEN 1 ELSE 0 END AS unmatched_territory
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
  -- The table's search box. Bound, never spliced, so a reader typing % or _ is
  -- searching for those characters rather than writing a pattern of their own.
  -- SQLite's LIKE is case-insensitive for ASCII, so "viet" finds "Viet Nam"
  -- without lowering either side.
  AND (:q IS NULL OR COALESCE(country_name, country_id) LIKE '%' || :q || '%')
