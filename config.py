"""Paths and constants. Imported by db.py and the app factory."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Supplied WHO data. Read only, never modified, committed to the repository.
SOURCE_DB = os.path.join(BASE_DIR, "immunisation2.db")

# Working database. Rebuilt from SOURCE_DB + sql/ by rebuild_db.sh. Git-ignored
# because it is binary and git cannot merge it; the state lives in sql/.
# IMMUATLAS_DB overrides it for tests or a throwaway copy.
DB_PATH = os.environ.get("IMMUATLAS_DB", os.path.join(BASE_DIR, "immuatlas.db"))

# One .sql file per named query (CLAUDE.md section 3).
QUERIES_DIR = os.path.join(BASE_DIR, "queries")

SITE_NAME = "ImmuAtlas"
SITE_TAGLINE = "Investigating preventable infectious diseases"

# Provenance shown in the footer. Deliberately NOT numbers: CLAUDE.md rule 7.2
# says every figure on a page comes from a query, so the year range and country
# count get wired to a query once queries/landing_facts.sql exists.
SOURCE_NAME = "World Health Organization Immunization Data"
SOURCE_URL = "https://immunizationdata.who.int/"

# Social links for the footer. Empty on purpose: this project has no accounts,
# and a footer full of links that go nowhere is worse than a footer without
# them. Add real ones here as ("Label", "https://...") and the block fills in.
SOCIAL_LINKS = []
