SELECT
    country_name,
    disease_name,
    year,
    cases,
    cases_per_100k
FROM v_infection
WHERE economy_phase = :economy
  AND inf_type = :infection_type
  AND year = :year
  AND cases_per_100k IS NOT NULL
ORDER BY cases_per_100k DESC
LIMIT 10;