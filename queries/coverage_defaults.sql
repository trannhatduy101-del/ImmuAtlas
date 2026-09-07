-- Sensible opening filters, so page 2A never presents an empty first view
-- (CLAUDE.md section 8, and definition of done item 1).
--
-- The default year is the most recent year that actually carries coverage
-- figures, not simply MAX(year): the newest year in the data may be a row of
-- blanks. The default antigen is the one most widely reported in that year, so
-- the first thing a visitor sees is the fullest picture available.
WITH latest AS (
    SELECT MAX(year) AS year FROM v_coverage WHERE coverage_reported IS NOT NULL
)
SELECT
    (SELECT year FROM latest) AS default_year,
    (SELECT vc.antigen
       FROM v_coverage vc
      WHERE vc.year = (SELECT year FROM latest)
        AND vc.coverage_reported IS NOT NULL
      GROUP BY vc.antigen
      ORDER BY COUNT(*) DESC, vc.antigen
      LIMIT 1) AS default_antigen;
