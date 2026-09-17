-- 2B: total cases for the selected disease/year, broken out by EVERY economic
-- phase side by side (brief example: "List the total number of cases of
-- rubella for each economic phase in the year 2010"). infections_economy_summary
-- answers the single phase the user picked; this answers all of them at once,
-- the same way coverage_by_region.sql shows every region regardless of which
-- one is selected on 2A.
-- The two anomaly counts are reported BESIDE the total, never subtracted from
-- it. A suspicious zero is our documented heuristic, not a known error, so
-- removing those rows would move every published figure on the strength of a
-- guess. Counting them lets the page say how much of the total rests on rows
-- worth checking.
--
-- No ORDER BY here: the route appends one from a whitelist so the reader can
-- sort this table (PHASE_SORT_KEYS in routes/infections.py).
SELECT
    economy_phase,
    COUNT(DISTINCT country_name)                         AS country_count,
    SUM(cases)                                            AS total_cases,
    SUM(national_population)                              AS total_population,
    ROUND(
        SUM(cases) * 100000.0 / NULLIF(SUM(national_population), 0),
        2
    )                                                      AS infection_rate_per_100k,
    SUM(CASE WHEN value_status = 'suspicious_zero' THEN 1 ELSE 0 END)
                                                           AS n_suspicious_zero,
    SUM(rate_unavailable)                                  AS n_no_population
FROM v_infection
WHERE inf_type = :infection_type
  AND year = :year
GROUP BY economy_phase
