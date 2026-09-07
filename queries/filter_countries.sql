-- Countries that appear in the coverage data, with their region so the form can
-- warn when a country and a region are selected that do not go together.
--
-- country_name is NULL for the nine territories present in Vaccination but
-- absent from Country. COALESCE keeps them selectable under their raw code
-- instead of dropping them from the list (CLAUDE.md 4.4).
SELECT DISTINCT
    vc.country_id,
    COALESCE(vc.country_name, vc.country_id) AS country_name,
    vc.region_id,
    vc.region_name
FROM v_coverage vc
WHERE vc.country_id IS NOT NULL
ORDER BY 2;
