-- Options for the antigen selector. Read from the view so an antigen that
-- exists in the lookup table but never appears in the data is not offered as a
-- filter that would return nothing.
SELECT DISTINCT
    vc.antigen,
    COALESCE(vc.antigen_name, vc.antigen) AS antigen_name,
    vc.inf_type,
    vc.disease_name
FROM v_coverage vc
WHERE vc.antigen IS NOT NULL
ORDER BY vc.disease_name, vc.antigen;
