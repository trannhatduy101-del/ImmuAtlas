-- 2A: regional summary, shown ABOVE the country table.
--
-- A national average hides subnational variation, so the regional figure is the
-- honest headline and the country table is the detail underneath.
--
-- TWO THINGS IN HERE ARE EASY TO GET WRONG:
--
-- 1. The filters on the coverage data sit in the ON clause, not in WHERE. A
--    condition on the right-hand table of a LEFT JOIN, placed in WHERE, throws
--    away the unmatched rows and quietly turns the LEFT JOIN into an INNER
--    JOIN. Kept in ON, a region with nothing to report still returns a row and
--    shows 0 instead of disappearing. Only the region filter itself, which
--    tests the left-hand table, belongs in WHERE.
--
-- 2. avg_unweighted is a mean of national percentages, so a country of 60,000
--    counts the same as one of 200 million. avg_weighted weights each national
--    figure by the birth cohort the rate actually applies to. They are both
--    shown because the difference between them is the point: quoting the
--    unweighted mean of a region with one huge country in it is how a regional
--    figure ends up wrong.
SELECT
    r.RegionID                                    AS region_id,
    r.region                                      AS region_name,
    COUNT(DISTINCT vc.country_id)                 AS n_countries,
    COUNT(vc.coverage_reported)                   AS n_reporting,
    ROUND(AVG(vc.coverage_reported), 2)           AS avg_unweighted,
    ROUND(
        SUM(vc.coverage_reported * vc.target_cohort)
        / NULLIF(SUM(CASE WHEN vc.coverage_reported IS NOT NULL
                          THEN vc.target_cohort END), 0)
    , 2)                                          AS avg_weighted,
    SUM(CASE WHEN vc.coverage_reported IS NOT NULL
             THEN vc.target_cohort END)           AS cohort_weighted
FROM Region r
LEFT JOIN v_coverage vc
       ON vc.region_id = r.RegionID
      AND (:antigen IS NULL OR vc.antigen    = :antigen)
      AND (:year    IS NULL OR vc.year       = :year)
      AND (:country IS NULL OR vc.country_id = :country)
WHERE (:region IS NULL OR r.RegionID = :region)
GROUP BY r.RegionID, r.region

UNION ALL

-- The territories present in the vaccination data but absent from Country have
-- no region at all. They are surfaced as their own row rather than dropped
-- (CLAUDE.md 4.4). Suppressed when a specific region is being viewed.
SELECT
    NULL, 'Not classified',
    COUNT(DISTINCT vc.country_id),
    COUNT(vc.coverage_reported),
    ROUND(AVG(vc.coverage_reported), 2),
    ROUND(
        SUM(vc.coverage_reported * vc.target_cohort)
        / NULLIF(SUM(CASE WHEN vc.coverage_reported IS NOT NULL
                          THEN vc.target_cohort END), 0)
    , 2),
    SUM(CASE WHEN vc.coverage_reported IS NOT NULL THEN vc.target_cohort END)
FROM v_coverage vc
WHERE vc.region_id IS NULL
  AND :region IS NULL
  AND (:antigen IS NULL OR vc.antigen    = :antigen)
  AND (:year    IS NULL OR vc.year       = :year)
  AND (:country IS NULL OR vc.country_id = :country)
HAVING COUNT(*) > 0;
