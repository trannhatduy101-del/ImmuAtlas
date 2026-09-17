-- 3A: biggest improvement in reported coverage for one antigen between a start
-- and an end year, with the matching change in reported case rate so the page
-- can ask whether disease burden ACTUALLY fell -- the Level-3 "use one result
-- to find another sub-dataset" step.
--
-- Every figure comes from the cleaned views (v_coverage / v_infection), so the
-- empty-string trap is already handled. A country is included only if it has a
-- real coverage figure at BOTH endpoints: the inner self-join on v_coverage
-- plus the two NOT NULL tests drop anyone missing either year, so no country
-- can appear from nowhere and show infinite improvement (stated on the page).
--
-- The case-rate columns are LEFT JOINed on the antigen's own disease
-- (cs.inf_type), so a country with coverage but no usable case rate still
-- ranks -- its case change simply reads "no data" rather than removing it.
--
-- Bound params: :antigen, :start_year, :end_year (and :limit, appended with the
-- whitelisted ORDER BY in the route -- a column name cannot be a bound value).
-- improvement_rank stays on coverage_reported, NOT on doses_per_100_change.
-- Ranking on the population denominator would change every figure on the page,
-- change which country leads, and make "coverage" mean one thing here and
-- another on 2A. The brief asks for a population-aware rate, not for the
-- ranking to be rebuilt on it, so both denominators are reported and only one
-- of them orders the table.
--
-- improvement_rank is computed in SQL, by coverage gain, ALWAYS -- never by
-- whatever the reader last sorted the table by. That is the whole point: a
-- Python enumerate() would renumber the rows under every sort, so "rank 3"
-- would mean something different on each view. Ranking here means a country
-- keeps its rank when the table is re-sorted or paged, and "biggest improver"
-- is simply improvement_rank = 1. Window functions need SQLite 3.25+; the
-- version bundled with Python 3.10+ is well past that.
SELECT
    cs.country_id,
    cs.country_name,
    cs.region_name,
    -- Used by the globe to group each region's countries into one click target.
    cs.region_id,
    -- On the table since :antigen became optional. With "all antigens" a
    -- country has one row per vaccine, and without this column those rows are
    -- the same name repeated with different numbers beside it.
    cs.antigen,
    cs.antigen_name,
    RANK() OVER (
        ORDER BY ROUND(ce.coverage_reported - cs.coverage_reported, 2) DESC
    )                                                       AS improvement_rank,
    cs.coverage_reported                                    AS coverage_start,
    ce.coverage_reported                                    AS coverage_end,
    ROUND(ce.coverage_reported - cs.coverage_reported, 2)   AS coverage_change,
    cs.national_population                                  AS population_start,
    ce.national_population                                  AS population_end,
    -- The brief's population-based reading of "vaccination rate". v_coverage
    -- already computes it (doses per 100 of the WHOLE national population), so
    -- it is read here, never recalculated. It is NOT coverage: its denominator
    -- is everyone alive, not the birth cohort the doses were aimed at, so the
    -- two columns are shown side by side and labelled, never mixed.
    cs.doses_per_100_population                             AS doses_per_100_start,
    ce.doses_per_100_population                             AS doses_per_100_end,
    ROUND(ce.doses_per_100_population - cs.doses_per_100_population, 4)
                                                            AS doses_per_100_change,
    isf.cases_per_100k                                      AS cases_start,
    ief.cases_per_100k                                      AS cases_end,
    ROUND(ief.cases_per_100k - isf.cases_per_100k, 2)       AS case_change
FROM v_coverage cs
JOIN v_coverage ce
      ON ce.country_id = cs.country_id
     AND ce.antigen    = cs.antigen
     AND ce.year       = :end_year
LEFT JOIN v_infection isf
      ON isf.country_id = cs.country_id
     AND isf.inf_type   = cs.inf_type
     AND isf.year       = :start_year
LEFT JOIN v_infection ief
      ON ief.country_id = cs.country_id
     AND ief.inf_type   = cs.inf_type
     AND ief.year       = :end_year
-- :antigen NULL ranks every vaccine at once, one row per country per antigen.
-- The rank then belongs to a country-and-vaccine pair, which is what the
-- antigen column on the table says.
WHERE (:antigen IS NULL OR cs.antigen   = :antigen)
  AND (:region  IS NULL OR cs.region_id = :region)
  AND cs.year    = :start_year
  AND cs.coverage_reported IS NOT NULL
  AND ce.coverage_reported IS NOT NULL
  -- The table's search box. Bound, never spliced, so a reader typing % or _ is
  -- searching for those characters rather than writing a pattern of their own.
  -- SQLite's LIKE is case-insensitive for ASCII, so "viet" finds "Viet Nam"
  -- without lowering either side.
  AND (:q IS NULL OR cs.country_name LIKE '%' || :q || '%')
