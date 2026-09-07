-- 1A landing page: the four facts.
--
-- CLAUDE.md section 8 fixes the count at exactly four, and rule 7.2 says every
-- number on the page comes from a query. Nothing here is typed into a template,
-- so deleting year 2024 from the database moves the range and changes the
-- figures. That is the mutation test.
--
-- Reads v_coverage and v_infection, never Vaccination or InfectionData: the raw
-- tables store missing values as empty strings and AVG() counts them as zero
-- (CLAUDE.md 4.1).
SELECT
    (SELECT MIN(year) FROM v_coverage)                      AS year_min,
    (SELECT MAX(year) FROM v_coverage)                      AS year_max,

    -- Countries that actually reported vaccination data. Territories present in
    -- Vaccination but absent from Country are kept by the view's LEFT JOIN and
    -- counted here, because they reported (CLAUDE.md 4.4).
    (SELECT COUNT(DISTINCT country_id) FROM v_coverage)     AS n_countries,

    -- Doses delivered. Blanks are already NULL in the view, and SUM skips NULL.
    (SELECT SUM(doses) FROM v_coverage)                     AS total_doses,

    (SELECT ROUND(AVG(coverage_reported), 1) FROM v_coverage
      WHERE year = (SELECT MIN(year) FROM v_coverage))      AS coverage_first,
    (SELECT ROUND(AVG(coverage_reported), 1) FROM v_coverage
      WHERE year = (SELECT MAX(year) FROM v_coverage))      AS coverage_last,

    -- Reported cases across the three diseases. A zero adds nothing to a sum, so
    -- this figure is unaffected by the reported-zero question of CLAUDE.md 4.3.
    (SELECT SUM(cases) FROM v_infection)                    AS total_cases,
    (SELECT COUNT(DISTINCT inf_type) FROM v_infection)      AS n_diseases;
