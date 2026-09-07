-- Years present in the coverage data, newest first so the default lands on the
-- most recent year rather than the year 2000.
SELECT DISTINCT year FROM v_coverage WHERE year IS NOT NULL ORDER BY year DESC;
