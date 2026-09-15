-- 2B: total cases for the selected disease/year, broken out by EVERY economic
-- phase side by side (brief example: "List the total number of cases of
-- rubella for each economic phase in the year 2010"). infections_economy_summary
-- answers the single phase the user picked; this answers all of them at once,
-- the same way coverage_by_region.sql shows every region regardless of which
-- one is selected on 2A.
SELECT
    economy_phase,
    COUNT(DISTINCT country_name)                         AS country_count,
    SUM(cases)                                            AS total_cases,
    SUM(national_population)                              AS total_population,
    ROUND(
        SUM(cases) * 100000.0 / NULLIF(SUM(national_population), 0),
        2
    )                                                      AS infection_rate_per_100k
FROM v_infection
WHERE inf_type = :infection_type
  AND year = :year
GROUP BY economy_phase
ORDER BY total_cases DESC;
