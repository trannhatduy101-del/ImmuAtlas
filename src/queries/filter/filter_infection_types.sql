SELECT DISTINCT inf_type, disease_name
FROM v_infection
WHERE inf_type IS NOT NULL
ORDER BY disease_name;
