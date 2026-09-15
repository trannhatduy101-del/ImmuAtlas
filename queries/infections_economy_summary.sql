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
    ) AS infection_rate_per_100k
FROM v_infection
WHERE economy_phase = :economy
  AND inf_type = :infection_type
  AND year = :year
GROUP BY economy_phase, year, disease_name;
