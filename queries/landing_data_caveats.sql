-- 1A: "what this data can and cannot tell you", measured rather than asserted.
--
-- Each figure is the size of a documented limitation from CLAUDE.md section 4,
-- counted live so the block cannot drift out of date with the database.
SELECT
    (SELECT COUNT(*) FROM v_coverage WHERE coverage_reported IS NULL)      AS rows_no_coverage,
    (SELECT COUNT(*) FROM v_coverage)                                     AS rows_coverage_total,
    (SELECT COUNT(*) FROM v_coverage WHERE coverage_above_100 = 1)        AS rows_above_100,
    (SELECT COUNT(*) FROM v_coverage WHERE country_name IS NULL)          AS rows_unmatched_territory,
    (SELECT COUNT(*) FROM v_infection WHERE value_status = 'suspicious_zero') AS rows_suspicious_zero,
    (SELECT COUNT(*) FROM v_infection)                                    AS rows_infection_total,
    (SELECT COUNT(DISTINCT country_id) FROM v_coverage
      WHERE economy_phase = 'Not classified')                             AS countries_no_economy;
