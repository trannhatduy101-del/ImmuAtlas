-- 2A: what the current selection actually contains.
--
-- Drives the "N countries reported nothing for this selection" line. Without
-- it, a country with a blank coverage figure is indistinguishable from a
-- country that is simply absent, and the table looks more complete than it is.
SELECT
    COUNT(*)                          AS n_rows,
    COUNT(coverage_reported)          AS n_with_coverage,
    COUNT(*) - COUNT(coverage_reported) AS n_without_coverage,
    COUNT(DISTINCT country_id)        AS n_countries,
    COUNT(DISTINCT CASE WHEN coverage_reported IS NOT NULL
                        THEN country_id END) AS n_countries_reporting,
    SUM(coverage_above_100)           AS n_above_100,
    MIN(year)                         AS year_min,
    MAX(year)                         AS year_max
FROM v_coverage
WHERE (:antigen IS NULL OR antigen    = :antigen)
  AND (:year    IS NULL OR year       = :year)
  AND (:country IS NULL OR country_id = :country)
  AND (:region  IS NULL OR region_id  = :region);
