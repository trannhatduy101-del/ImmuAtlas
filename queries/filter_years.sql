-- Years available in the infection dataset, newest first.
SELECT DISTINCT year
FROM v_infection
WHERE year IS NOT NULL
ORDER BY year DESC;