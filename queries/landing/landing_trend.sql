-- 1A: coverage and reported cases per year, for the trend snapshot.
--
-- Joins two genuinely different datasets, vaccination effort against disease
-- outcome, so the page can say something neither shows alone. LEFT JOIN, so a
-- year with coverage but no infection rows still appears rather than vanishing.
--
-- n_reporting is carried because it is the honest caveat: a rise in the average
-- can mean more countries reported, not that more children were vaccinated.
SELECT
    c.year,
    c.avg_coverage,
    c.n_reporting,
    i.total_cases
FROM (
    SELECT year,
           ROUND(AVG(coverage_reported), 2) AS avg_coverage,
           COUNT(coverage_reported)         AS n_reporting
    FROM v_coverage
    GROUP BY year
) c
LEFT JOIN (
    SELECT year, SUM(cases) AS total_cases
    FROM v_infection
    GROUP BY year
) i ON i.year = c.year
ORDER BY c.year;
