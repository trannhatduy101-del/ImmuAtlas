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
             THEN 1 ELSE 0 END)                          AS n_met,

    -- The two above count ROWS, which is what the average and the chart need.
    -- These two count COUNTRIES, which is what a sentence saying "countries"
    -- needs. They differ the moment a selection spans more than one antigen or
    -- more than one year: with all antigens in 2015 the row count is 791 and
    -- the country count is 182, and printing the first beside the word
    -- "countries" overstates the site by a factor of four.
    --
    -- COUNT(DISTINCT ...) not SUM(CASE ...), matching n_met_threshold in
    -- coverage_by_region.sql, so the two "met the threshold" figures on this
    -- one page finally count the same thing. The consequence to state on the
    -- page: across several years a country counts as having met the threshold
    -- if it did so in at least one of them.
    COUNT(DISTINCT country_id)                           AS n_countries_reporting,
    COUNT(DISTINCT CASE WHEN coverage_reported >= threshold_pct
                        THEN country_id END)             AS n_countries_met
FROM v_herd_immunity
WHERE (:antigen IS NULL OR antigen    = :antigen)
  AND (:year    IS NULL OR year       = :year)
  AND (:country IS NULL OR country_id  = :country)
  AND (:region  IS NULL OR region_id   = :region)
  AND coverage_reported IS NOT NULL;
