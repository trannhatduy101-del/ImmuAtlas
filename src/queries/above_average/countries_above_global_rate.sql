WITH country_rates AS (
    SELECT
        country_name,
        disease_name,
        year,
        CAST(SUM(cases) AS INTEGER) AS total_cases,
        CAST(MAX(national_population) AS INTEGER) AS population,
        SUM(cases) * 100000.0 /
            NULLIF(MAX(national_population), 0) AS country_rate
    FROM v_infection
    WHERE year = :year
      AND inf_type = :infection_type
    GROUP BY country_name, disease_name, year
),

global_rate AS (
    SELECT
        SUM(cases) * 100000.0 /
            NULLIF(SUM(national_population), 0) AS rate
    FROM v_infection
    WHERE year = :year
      AND inf_type = :infection_type
)

SELECT
    country_name,
    disease_name,
    year,
    total_cases,
    population,
    ROUND(country_rate, 2) AS country_rate_per_100k
FROM country_rates
WHERE country_rate > (
    SELECT rate
    FROM global_rate
)