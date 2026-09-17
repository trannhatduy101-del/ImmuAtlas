SELECT
    country_name,
    economy_phase,
    year,
    disease_name,
    cases,
    national_population,
    cases_per_100k,
    value_status
FROM v_infection
WHERE economy_phase = :economy
  AND inf_type = :infection_type
  AND year = :year