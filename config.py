"""Paths and constants. Imported by db.py and the app factory."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Supplied WHO data. Read only, never modified, committed to the repository.
SOURCE_DB = os.path.join(BASE_DIR, "immunisation2.db")

# Working database. Rebuilt from SOURCE_DB + sql/ by rebuild_db.py. Git-ignored
# because it is binary and git cannot merge it; the state lives in sql/.
# IMMUATLAS_DB overrides it for tests or a throwaway copy.
DB_PATH = os.environ.get("IMMUATLAS_DB", os.path.join(BASE_DIR, "immuatlas.db"))

# One .sql file per named query (the project spec section 3).
QUERIES_DIR = os.path.join(BASE_DIR, "queries")

SITE_NAME = "ImmuAtlas"
SITE_TAGLINE = "Investigating preventable infectious diseases"

# Provenance shown in the footer. Deliberately NOT numbers: the project spec rule 7.2
# says every figure on a page comes from a query, so the year range and country
# count get wired to a query once queries/landing_facts.sql exists.
SOURCE_NAME = "World Health Organization Immunization Data"
SOURCE_URL = "https://immunizationdata.who.int/"

# Links for the footer, as ("Label", "https://..."). No social accounts exist
# for this project, and a footer full of links that go nowhere is worse than a
# footer without them -- so this holds only the one link that does go
# somewhere: the source for the site itself.
SOCIAL_LINKS = [
    ("Project repository", "https://github.com/trannhatduy101-del/ImmuAtlas"),
]
