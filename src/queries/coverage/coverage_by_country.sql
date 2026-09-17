-- 2A: the country table.
--
-- Reads v_herd_immunity, which is v_coverage plus the sourced threshold and a
-- status label, so the benchmark sits beside every figure rather than in the
-- reader's head.
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
    economy_phase,
    year,
    antigen,
    antigen_name,
    disease_name,
    coverage_reported,
    coverage_vs_cohort,
    doses_per_100_population,
    target_cohort,
    doses,
    national_population,
    denominator_available,
    coverage_above_100,
    threshold_pct,
    threshold_source,
    herd_immunity_status,
    ROUND(coverage_reported - threshold_pct, 2) AS gap_to_threshold,
    CASE WHEN country_name IS NULL THEN 1 ELSE 0 END AS unmatched_territory
FROM v_herd_immunity
WHERE (:antigen IS NULL OR antigen    = :antigen)
  AND (:year    IS NULL OR year       = :year)
  AND (:country IS NULL OR country_id = :country)
  AND (:region  IS NULL OR region_id  = :region)
  -- Brief 2A, Table 1: "all countries that have MET at least 90% of their
  -- vaccination targets". Each row is compared against ITS OWN threshold_pct,
  -- never a literal 90: WHO sets 95 for measles, 90 for DTP and 80 for rubella,
  -- so a hardcoded 90 would list measles countries that did not in fact meet
  -- theirs. coverage_reported >= NULL is NULL, so a country that reported
  -- nothing falls out on its own -- which is right, "no figure" is not "met".
  AND (:met_only IS NULL OR coverage_reported >= threshold_pct)
