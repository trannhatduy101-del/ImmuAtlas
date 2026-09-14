-- 2A: the outcome verdict for the current selection.
--
-- One defensible line for the reader: the average of the reporting national
-- figures, and how many of them reached the threshold. Aggregated in SQL (never
-- in Python), over the SAME filters as the country table. Blanks are excluded
-- rather than counted as zero. n_thresholds tells the page whether a single
-- threshold applies (one antigen) so the "X met" verdict is meaningful.
SELECT
    ROUND(AVG(coverage_reported), 1)                     AS avg_coverage,
    COUNT(coverage_reported)                             AS n_reporting,
    COUNT(DISTINCT threshold_pct)                        AS n_thresholds,
    MAX(threshold_pct)                                   AS threshold_pct,
    SUM(CASE WHEN coverage_reported >= threshold_pct
             THEN 1 ELSE 0 END)                          AS n_met
FROM v_herd_immunity
WHERE (:antigen IS NULL OR antigen    = :antigen)
  AND (:year    IS NULL OR year       = :year)
  AND (:country IS NULL OR country_id  = :country)
  AND (:region  IS NULL OR region_id   = :region)
  AND coverage_reported IS NOT NULL;
