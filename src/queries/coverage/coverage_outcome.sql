-- 2A: the outcome verdict for the current selection.
--
-- One defensible line for the reader: the average of the reporting national
-- figures, and how many of them reached the threshold. Aggregated in SQL (never
-- in Python), over the SAME filters as the country table. Blanks are excluded
-- rather than counted as zero. :met_threshold is the single bar this page
-- measures against, so the verdict holds whether one antigen is selected or
-- all of them.
SELECT
    ROUND(AVG(coverage_reported), 1)                     AS avg_coverage,

    -- COUNTRIES, not rows. The two differ the moment a selection spans more
    -- than one antigen or more than one year: with all antigens in 2015 the row
    -- count is 791 and the country count is 182, and printing the first beside
    -- the word "countries" overstates the site by a factor of four. The row
    -- counts this query used to return alongside these were read by nothing.
    --
    -- COUNT(DISTINCT ...) not SUM(CASE ...), matching n_met_threshold in
    -- coverage_by_region.sql, so the two "met the target" figures on this one
    -- page count the same thing. The consequence to state on the page: across
    -- several years a country counts as having met the target if it did so in
    -- at least one of them.
    COUNT(DISTINCT country_id)                           AS n_countries_reporting,
    COUNT(DISTINCT CASE WHEN coverage_reported >= :met_threshold
                        THEN country_id END)             AS n_countries_met
FROM v_coverage
WHERE (:antigen IS NULL OR antigen    = :antigen)
  AND (:year    IS NULL OR year       = :year)
  AND (:country IS NULL OR country_id  = :country)
  AND (:region  IS NULL OR region_id   = :region)
  AND coverage_reported IS NOT NULL;
