-- =====================================================================
-- ImmuAtlas - schema additions
-- COSC3106 Studio Project
--
-- Adds the tables the brief requires but the supplied database lacks,
-- plus a view layer that solves the data problems once instead of in
-- six route functions.
--
-- Apply to a COPY of immunisation2.db:
--     cp immunisation2.db immuatlas.db
--     sqlite3 immuatlas.db < schema_immuatlas.sql
--     sqlite3 immuatlas.db < seed_immuatlas.sql
--
-- Safe to re-run. Nothing in the nine supplied tables is modified.
-- =====================================================================

PRAGMA foreign_keys = ON;


-- =====================================================================
-- PART 1  RESEARCH SOURCES
-- Every persona claim points at a row here. Brief 1B requires personas
-- to come out of the database; the rubric requires them to be
-- "informed by research", so the evidence lives in the database too.
-- =====================================================================

CREATE TABLE IF NOT EXISTS research_source (
    source_id     TEXT PRIMARY KEY,        -- 'S1' .. 'S8'
    authors       TEXT NOT NULL,
    year          INTEGER NOT NULL,
    title         TEXT NOT NULL,
    publication   TEXT NOT NULL,
    volume_issue  TEXT,
    doi           TEXT,
    url           TEXT,
    study_design  TEXT,                    -- so a claim can be weighed
    user_group    INTEGER,                 -- 1 general public, 2 intermediaries
    verified      INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0,1)),
    verified_note TEXT                     -- what the verification pass changed
);


-- =====================================================================
-- PART 2  PERSONAS
-- Field list kept generic on purpose: it must hold Daniel Nguyen
-- (Group 1, general public) as well as Grace Achieng (Group 2), and
-- the two personas do not carry the same attributes.
-- =====================================================================

CREATE TABLE IF NOT EXISTS user_group (
    group_id     INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    description  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS persona (
    persona_id      INTEGER PRIMARY KEY,
    group_id        INTEGER NOT NULL,
    name            TEXT NOT NULL,
    archetype       TEXT,
    age             INTEGER,
    role_title      TEXT,
    organisation    TEXT,
    location        TEXT,
    education       TEXT,
    experience      TEXT,
    quote           TEXT,
    bio             TEXT,
    trigger_context TEXT,        -- what brings them to the site today
    success_criterion TEXT,      -- what "done" looks like for them
    counterfactual  TEXT,        -- what happens if this site did not exist
    image_path      TEXT,
    image_credit    TEXT,        -- required if the photo is licensed
    owner_student   TEXT,        -- which team member owns this persona
    display_order   INTEGER DEFAULT 0,
    FOREIGN KEY (group_id) REFERENCES user_group(group_id)
);

-- Goals carry the page they map to, so page 1B can state which part of
-- the site exists for which persona, from data rather than hardcoded text.
CREATE TABLE IF NOT EXISTS persona_goal (
    goal_id     INTEGER PRIMARY KEY,
    persona_id  INTEGER NOT NULL,
    goal        TEXT NOT NULL,
    page_code   TEXT,                 -- '1A','2A','3A', or NULL for site-wide
    priority    INTEGER DEFAULT 1,
    source_id   TEXT,
    FOREIGN KEY (persona_id) REFERENCES persona(persona_id),
    FOREIGN KEY (source_id)  REFERENCES research_source(source_id)
);

CREATE TABLE IF NOT EXISTS persona_need (
    need_id     INTEGER PRIMARY KEY,
    persona_id  INTEGER NOT NULL,
    need        TEXT NOT NULL,
    priority    INTEGER DEFAULT 1,
    source_id   TEXT,
    FOREIGN KEY (persona_id) REFERENCES persona(persona_id),
    FOREIGN KEY (source_id)  REFERENCES research_source(source_id)
);

-- source_id is NOT NULL here by design: the checklist requires every
-- pain point to trace to the study behind it.
CREATE TABLE IF NOT EXISTS persona_pain (
    pain_id     INTEGER PRIMARY KEY,
    persona_id  INTEGER NOT NULL,
    pain_point  TEXT NOT NULL,
    evidence    TEXT,                 -- the specific figure, in words
    source_id   TEXT NOT NULL,
    FOREIGN KEY (persona_id) REFERENCES persona(persona_id),
    FOREIGN KEY (source_id)  REFERENCES research_source(source_id)
);

-- One generic table for every 0-100 scale: working profile axes,
-- where their figures come from, trust criteria, motivations.
-- Three categories share one shape, so one table keeps this in 3NF and
-- lets a new category be added with no schema change.
CREATE TABLE IF NOT EXISTS persona_attribute (
    attribute_id  INTEGER PRIMARY KEY,
    persona_id    INTEGER NOT NULL,
    category      TEXT NOT NULL
        CHECK (category IN ('profile','source_used','trust_criterion','motivation')),
    label         TEXT NOT NULL,
    value         INTEGER NOT NULL CHECK (value BETWEEN 0 AND 100),
    anchor_note   TEXT,
    source_id     TEXT,
    display_order INTEGER DEFAULT 0,
    FOREIGN KEY (persona_id) REFERENCES persona(persona_id),
    FOREIGN KEY (source_id)  REFERENCES research_source(source_id)
);

-- Free-text persona items that are lists rather than scales.
CREATE TABLE IF NOT EXISTS persona_note (
    note_id     INTEGER PRIMARY KEY,
    persona_id  INTEGER NOT NULL,
    category    TEXT NOT NULL
        CHECK (category IN ('anti_goal','behaviour','skill_tag','tag')),
    note        TEXT NOT NULL,
    source_id   TEXT,
    display_order INTEGER DEFAULT 0,
    FOREIGN KEY (persona_id) REFERENCES persona(persona_id),
    FOREIGN KEY (source_id)  REFERENCES research_source(source_id)
);


-- =====================================================================
-- PART 3  TEAM
-- Brief 1B: names and student numbers must be stored in and retrieved
-- from the database.
-- =====================================================================

CREATE TABLE IF NOT EXISTS team_member (
    student_number TEXT PRIMARY KEY,
    full_name      TEXT NOT NULL,
    sub_task       TEXT,               -- 'A' or 'B'
    responsibility TEXT,
    display_order  INTEGER DEFAULT 0
);


-- =====================================================================
-- PART 4  HERD IMMUNITY THRESHOLDS
-- Brief 2A asks for "herd immunity levels". The supplied data has none,
-- so the thresholds are sourced and stored rather than hardcoded.
-- =====================================================================

CREATE TABLE IF NOT EXISTS herd_immunity_threshold (
    inf_type      TEXT PRIMARY KEY,
    threshold_pct REAL NOT NULL CHECK (threshold_pct BETWEEN 0 AND 100),
    source        TEXT NOT NULL,
    source_url    TEXT,
    note          TEXT,
    FOREIGN KEY (inf_type) REFERENCES Infection_Type(id)
);


-- =====================================================================
-- PART 5  VIEW LAYER
--
-- These exist because the supplied data has three traps that will
-- silently produce wrong numbers if every route function has to
-- remember them:
--
--   1. Missing values in Vaccination are stored as EMPTY STRINGS, not
--      NULL. SQLite orders TEXT above every number, so `IS NULL` finds
--      none of them, AVG() counts them as zero, MAX() returns '', and
--      `coverage > 100` matches every blank.
--      Measured: AVG(coverage) = 68.52 raw vs 88.26 cleaned.
--
--   2. There are TWO possible denominators and they mean different
--      things. target_num is the birth cohort (median 1.85% of national
--      population). Dividing doses by total population instead gives
--      ~2%, which is not a coverage rate at all.
--
--   3. InfectionData is a complete 207x3x25 grid with no NULLs, but
--      7,156 of 15,525 values (46.1%) are exactly zero. A reported zero
--      and an unreported year are indistinguishable in the raw data.
-- =====================================================================

-- ---------------------------------------------------------------------
-- v_coverage
-- Empty strings converted to real NULLs. BOTH denominators exposed and
-- labelled, because the brief (3A) requires a rate that "depends on the
-- population of the country" while the reported coverage figure uses
-- the birth cohort. Page code must state which one it used.
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_coverage;
CREATE VIEW v_coverage AS
SELECT
    v.country                                        AS country_id,
    c.name                                           AS country_name,
    c.region                                         AS region_id,
    r.region                                         AS region_name,
    CASE WHEN typeof(c.economy)='integer' THEN c.economy END AS economy_id,
    COALESCE(e.phase, 'Not classified')              AS economy_phase,
    v.year,
    v.antigen,
    a.name                                           AS antigen_name,
    v.inf_type,
    t.description                                    AS disease_name,

    -- cleaned source columns
    CASE WHEN typeof(v.target_num) IN ('integer','real') THEN v.target_num END AS target_cohort,
    CASE WHEN typeof(v.doses)      IN ('integer','real') THEN v.doses      END AS doses,
    CASE WHEN typeof(v.coverage)   IN ('integer','real') THEN v.coverage   END AS coverage_reported,

    p.population                                     AS national_population,

    -- DENOMINATOR 1: birth cohort. This is what WHO reports as coverage.
    CASE WHEN typeof(v.doses) IN ('integer','real')
          AND typeof(v.target_num) IN ('integer','real')
          AND v.target_num > 0
         THEN ROUND(v.doses * 100.0 / v.target_num, 2) END  AS coverage_vs_cohort,

    -- DENOMINATOR 2: whole national population. NOT a coverage rate --
    -- it is doses delivered per 100 people of all ages. Provided so a
    -- page can satisfy a population-based reading of the brief while
    -- labelling it honestly.
    CASE WHEN typeof(v.doses) IN ('integer','real') AND p.population > 0
         THEN ROUND(v.doses * 100.0 / p.population, 4) END   AS doses_per_100_population,

    -- which denominator is available for this row
    CASE
      WHEN typeof(v.target_num) IN ('integer','real') AND v.target_num > 0
           AND p.population > 0 THEN 'both'
      WHEN typeof(v.target_num) IN ('integer','real') AND v.target_num > 0 THEN 'cohort_only'
      WHEN p.population > 0 THEN 'population_only'
      ELSE 'none'
    END                                              AS denominator_available,

    -- the population figure is the same year as the doses, never a proxy year
    v.year                                           AS denominator_year,

    CASE WHEN typeof(v.coverage) IN ('integer','real') AND v.coverage > 100
         THEN 1 ELSE 0 END                           AS coverage_above_100

FROM Vaccination v
LEFT JOIN Country           c ON v.country = c.CountryID
LEFT JOIN Region            r ON c.region  = r.RegionID
LEFT JOIN Economy           e ON CASE WHEN typeof(c.economy)='integer'
                                      THEN c.economy END = e.economyID
LEFT JOIN Antigen           a ON v.antigen  = a.AntigenID
LEFT JOIN Infection_Type    t ON v.inf_type = t.id
LEFT JOIN CountryPopulation p ON v.country = p.country AND v.year = p.year;


-- ---------------------------------------------------------------------
-- v_infection
-- Carries a flag separating a reported zero from a probably-missing
-- value. The raw data cannot distinguish them, so the flag is an
-- explicit, documented heuristic:
--   a zero is 'suspicious' when that country reports zero for that
--   disease in EVERY year of the series.
-- 20-28 countries per disease meet that test. This is a judgement, not
-- a fact from the data, and any page using it must say so.
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_infection;
CREATE VIEW v_infection AS
WITH always_zero AS (
    SELECT inf_type, country
    FROM InfectionData
    GROUP BY inf_type, country
    HAVING SUM(cases) = 0 AND COUNT(*) = (SELECT COUNT(*) FROM YearDate)
)
SELECT
    i.country                                   AS country_id,
    c.name                                      AS country_name,
    c.region                                    AS region_id,
    r.region                                    AS region_name,
    CASE WHEN typeof(c.economy)='integer' THEN c.economy END AS economy_id,
    COALESCE(e.phase, 'Not classified')         AS economy_phase,
    i.year,
    i.inf_type,
    t.description                               AS disease_name,
    i.cases,
    p.population                                AS national_population,

    CASE WHEN p.population > 0
         THEN ROUND(i.cases * 100000.0 / p.population, 2) END AS cases_per_100k,

    -- 'reported'         value greater than zero
    -- 'reported_zero'    zero, but this country reports non-zero in other years
    -- 'suspicious_zero'  zero in every year of the series for this disease
    CASE
      WHEN i.cases > 0 THEN 'reported'
      WHEN az.country IS NOT NULL THEN 'suspicious_zero'
      ELSE 'reported_zero'
    END                                         AS value_status,

    CASE WHEN p.population IS NULL OR p.population = 0 THEN 1 ELSE 0 END
                                                AS rate_unavailable

FROM InfectionData i
LEFT JOIN Country           c ON i.country = c.CountryID
LEFT JOIN Region            r ON c.region  = r.RegionID
LEFT JOIN Economy           e ON CASE WHEN typeof(c.economy)='integer'
                                      THEN c.economy END = e.economyID
LEFT JOIN Infection_Type    t ON i.inf_type = t.id
LEFT JOIN CountryPopulation p ON i.country = p.country AND i.year = p.year
LEFT JOIN always_zero      az ON az.inf_type = i.inf_type AND az.country = i.country;


-- ---------------------------------------------------------------------
-- v_herd_immunity  -- coverage measured against the sourced threshold
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_herd_immunity;
CREATE VIEW v_herd_immunity AS
SELECT
    vc.*,
    h.threshold_pct,
    h.source        AS threshold_source,
    CASE
      WHEN vc.coverage_reported IS NULL              THEN 'No data'
      WHEN h.threshold_pct IS NULL                   THEN 'No threshold set'
      WHEN vc.coverage_reported >= h.threshold_pct   THEN 'At or above threshold'
      ELSE 'Below threshold'
    END AS herd_immunity_status
FROM v_coverage vc
LEFT JOIN herd_immunity_threshold h ON vc.inf_type = h.inf_type;


-- ---------------------------------------------------------------------
-- v_persona_full  -- one row per persona for page 1B
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_persona_full;
CREATE VIEW v_persona_full AS
SELECT
    p.*,
    g.name        AS group_name,
    g.description AS group_description,
    (SELECT COUNT(*) FROM persona_goal x WHERE x.persona_id = p.persona_id) AS n_goals,
    (SELECT COUNT(*) FROM persona_need x WHERE x.persona_id = p.persona_id) AS n_needs,
    (SELECT COUNT(*) FROM persona_pain x WHERE x.persona_id = p.persona_id) AS n_pains,
    (SELECT COUNT(DISTINCT source_id) FROM persona_pain x
      WHERE x.persona_id = p.persona_id)                                    AS n_sources_cited
FROM persona p
JOIN user_group g ON p.group_id = g.group_id;


-- =====================================================================
-- PART 6  INDEXES  (brief L3: "Write an efficient SQL query")
-- =====================================================================

CREATE INDEX IF NOT EXISTS idx_vacc_country_year  ON Vaccination(country, year);
CREATE INDEX IF NOT EXISTS idx_vacc_antigen_year  ON Vaccination(antigen, year);
CREATE INDEX IF NOT EXISTS idx_vacc_inf_year      ON Vaccination(inf_type, year);
CREATE INDEX IF NOT EXISTS idx_inf_type_year      ON InfectionData(inf_type, year);
CREATE INDEX IF NOT EXISTS idx_inf_country_year   ON InfectionData(country, year);
CREATE INDEX IF NOT EXISTS idx_pop_country_year   ON CountryPopulation(country, year);
