SELECT DISTINCT economy_phase
FROM v_infection
WHERE economy_phase IS NOT NULL
ORDER BY economy_phase;