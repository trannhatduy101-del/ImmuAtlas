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
    -- Status and gap are both measured against :met_threshold, the one bar this
    -- page uses. If they disagreed, the pill would call a country "below" while
    -- the filter had already let it through.
    CASE
      WHEN coverage_reported IS NULL                 THEN 'No figure reported'
      WHEN coverage_reported >= :met_threshold       THEN 'At or above target'
      ELSE 'Below target'
    END                                          AS herd_immunity_status,
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
  -- cited in the method note; nothing here is filtered or counted with them. coverage_reported >= NULL is NULL, so a country that
  -- reported nothing falls out on its own: "no figure" is not "met".
  AND (:met_only IS NULL OR coverage_reported >= :met_threshold)
