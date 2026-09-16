SELECT
    economy_phase,
    year,
    disease_name,
    COUNT(DISTINCT country_name) AS country_count,
    SUM(cases) AS total_cases,
    SUM(national_population) AS total_population,
    ROUND(
        SUM(cases) * 100000.0 / NULLIF(SUM(national_population), 0),
        2
    ) AS infection_rate_per_100k,
    -- Counted beside the total, never removed from it: a suspicious zero is a
    -- documented heuristic of ours, not a known error in the source.
    SUM(CASE WHEN value_status = 'suspicious_zero' THEN 1 ELSE 0 END)
                                      AS n_suspicious_zero,
    SUM(rate_unavailable)             AS n_no_population
FROM v_infection
WHERE economy_phase = :economy
  AND inf_type = :infection_type
  AND year = :year
GROUP BY economy_phase, year, disease_name;
