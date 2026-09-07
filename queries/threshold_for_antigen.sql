-- The herd immunity threshold that applies to one antigen, with its citation.
--
-- The threshold is never a literal in the code: it lives in
-- herd_immunity_threshold, sourced from a WHO position paper, so the page can
-- print where the number came from. LEFT JOIN, so an antigen whose disease has
-- no threshold on file returns a row saying so rather than no row at all.
SELECT DISTINCT
    vc.inf_type,
    vc.disease_name,
    h.threshold_pct,
    h.source     AS threshold_source,
    h.source_url AS threshold_url,
    h.note       AS threshold_note
FROM v_coverage vc
LEFT JOIN herd_immunity_threshold h ON h.inf_type = vc.inf_type
WHERE vc.antigen = :antigen;
