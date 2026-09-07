-- =====================================================================
-- ImmuAtlas - WHO data provenance
--
-- The site displays two supplied datasets but cited neither of them
-- from the database: the footer named WHO in a hardcoded Python
-- string, which the checklist rules out. The citation component reads
-- the database, never a literal.
--
-- WHY A SEPARATE TABLE, NOT research_source:
--
--   research_source holds the evidence behind persona claims, and its
--   row count is part of the project's verification contract (8, and
--   it is checked). Adding provenance rows to it broke that check the
--   moment they went in.
--
--   The two things are also not the same kind of object. A row in
--   research_source is a study that supports an assertion about a
--   user. A row here is the origin of a number on the screen. Merging
--   them would mean "8 sources" could no longer be stated about
--   anything meaningful.
--
-- Applied after seed_immuatlas.sql. Safe to re-run.
--
--   WUENIC  ->  the Vaccination table
--   VPD     ->  the InfectionData table
--
-- BOTH ARE verified = 0, and the footer marks them as unverified on
-- every page until someone checks them. Two things are open:
--
--   1. The release year is a PLACEHOLDER. WUENIC revises historical
--      estimates every year, so the figures in immunisation2.db belong
--      to one specific release. Citing the wrong year misdates every
--      number on the site. Only the course coordinator knows which
--      release the supplied database was cut from.
--
--   2. The URLs have not been opened. who.int and
--      immunizationdata.who.int were unreachable from the environment
--      these rows were written in, so the titles come from search
--      results rather than from the pages themselves.
--
-- Set verified = 1 and record what you checked in verified_note only
-- after opening both URLs and confirming the release year.
-- =====================================================================

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS data_source (
    data_source_id TEXT PRIMARY KEY,
    publisher      TEXT NOT NULL,
    title          TEXT NOT NULL,
    publication    TEXT,
    release_year   INTEGER,
    url            TEXT,
    covers_table   TEXT,          -- which supplied table this is the origin of
    collection     TEXT,          -- how the data reaches the publisher
    caveat         TEXT,          -- what a page citing this must also say
    verified       INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0,1)),
    verified_note  TEXT,
    display_order  INTEGER DEFAULT 0
);

INSERT OR REPLACE INTO data_source
 (data_source_id, publisher, title, publication, release_year, url,
  covers_table, collection, caveat, verified, verified_note, display_order)
VALUES

('WUENIC', 'World Health Organization and UNICEF',
 'WHO/UNICEF Estimates of National Immunization Coverage (WUENIC)',
 'WHO Immunization Data portal', 2025,
 'https://immunizationdata.who.int/',
 'Vaccination',
 'Administrative reporting through the WHO/UNICEF electronic Joint Reporting Form, combined with national best estimates, coverage surveys, published and grey literature, and contextual factors including data quality audits and reported stockouts. Produced annually since 2001 for 195 countries across 15 vaccines, doses and antigens.',
 'These are estimates, not a census. Rau et al. 2022 (research_source S2) assessed this exact series and found anomalies in 47 percent of expected data points; denominators were the weakest element. A coverage figure here is the best available number, not a measured one.',
 0,
 'UNVERIFIED. Release year is a placeholder and the URL has not been opened. See the header of this file.',
 1),

('VPD', 'World Health Organization',
 'Vaccine-preventable disease incidence: reported cases of measles, pertussis and rubella',
 'WHO Immunization Data portal', 2025,
 'https://immunizationdata.who.int/',
 'InfectionData',
 'Annual counts of reported cases by country and year, compiled from case-based and aggregate national surveillance reported through the WHO/UNICEF electronic Joint Reporting Form. Measles and rubella are additionally reported monthly through provisional surveillance.',
 'A reported count of zero and a year with no report are indistinguishable in this data. v_infection.value_status separates them by an explicit heuristic of ours; that flag is our inference and must never be attributed to WHO.',
 0,
 'UNVERIFIED. Release year is a placeholder and the URL has not been opened. See the header of this file.',
 2);
