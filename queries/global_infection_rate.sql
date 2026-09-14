SELECT
    :year AS year,
    :infection_type AS inf_type,
    disease_name,
    CAST(SUM(cases) AS INTEGER) AS total_cases,
    CAST(SUM(national_population) AS INTEGER) AS total_population,
    ROUND(
        SUM(cases) * 100000.0 /
        NULLIF(SUM(national_population), 0),
        2
    ) AS global_rate_per_100k
FROM v_infection
WHERE year = :year
  AND inf_type = :infection_type
GROUP BY disease_name;