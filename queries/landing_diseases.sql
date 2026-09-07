-- 1A: the diseases covered, each with its sourced herd immunity threshold.
--
-- LEFT JOIN so a disease with no threshold on file still lists, showing "no
-- threshold set" rather than disappearing from the page (CLAUDE.md 4.4).
-- The threshold is never hardcoded: it and its citation live in
-- herd_immunity_threshold, seeded from WHO position papers.
SELECT
    t.id                AS inf_type,
    t.description       AS disease_name,
    h.threshold_pct,
    h.source            AS threshold_source,
    h.source_url        AS threshold_url,
    h.note              AS threshold_note,
    (SELECT COUNT(DISTINCT country_id) FROM v_infection vi
      WHERE vi.inf_type = t.id AND vi.value_status = 'reported') AS n_countries_reporting
FROM Infection_Type t
LEFT JOIN herd_immunity_threshold h ON h.inf_type = t.id
ORDER BY t.description;
