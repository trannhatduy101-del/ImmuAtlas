"""1B Mission statement -- Sub-Task B.

Brief 1B requires personas and team members to be stored in and retrieved
from the database. Team members were already DB-driven; this route reads
the full persona model (persona + its five child tables) instead of the
Python constant that used to hold the copy.
"""

import glob
import os
from collections import defaultdict

from flask import Blueprint, render_template

import config
import db

bp = Blueprint("mission", __name__)

# Which photo belongs to whom. A path on disk, not a database column: the brief
# requires the NAMES and STUDENT NUMBERS to come from the database, and they do
# -- a photograph is an asset like the persona portraits beside it. Keeping it
# out of the schema also means a teammate whose immuatlas.db predates this
# change still sees the photos, instead of silently missing a column.
TEAM_PHOTOS = {
    "s4160446": "duy-photo",
    "s4138996": "huy-photo",
}


def team_photo(student_number):
    """static/ path of this member's photo, or None if the file is not there.

    Matched by stem rather than by full filename so the image can be dropped in
    as .webp, .jpg or .png without touching this file, and a missing photo
    falls back to the text-only card instead of a broken image icon.
    """
    stem = TEAM_PHOTOS.get(student_number)
    if not stem:
        return None
    pattern = os.path.join(config.BASE_DIR, "static", "img", stem + ".*")
    found = sorted(glob.glob(pattern))
    return "img/" + os.path.basename(found[0]) if found else None

ATTRIBUTE_CATEGORIES = ("personality", "profile", "source_used",
                        "trust_criterion", "motivation")
NOTE_CATEGORIES = ("tag", "skill_tag", "behaviour", "anti_goal")


def _group_by_persona(rows, value_key=None):
    """{persona_id: [row, ...]}, or {persona_id: [row[value_key], ...]}."""
    out = defaultdict(list)
    for r in rows:
        out[r["persona_id"]].append(r[value_key] if value_key else r)
    return out


def _group_by_persona_and_category(rows, categories, field):
    """{persona_id: {category: [row, ...]}}, every category present (possibly empty)."""
    out = defaultdict(lambda: {cat: [] for cat in categories})
    for r in rows:
        out[r["persona_id"]][r["category"]].append(
            {"label": r["label"], "label_right": r["label_right"],
             "value": r["value"]} if field == "attribute"
            else r["note"]
        )
    return out


@bp.route("/mission")
def index():
    try:
        team_members = db.query(db.load_query("team_members"))
        persona_rows = db.query(db.load_query("persona_list"))
    except db.DatabaseMissing as exc:
        # A fresh clone has no immuatlas.db until rebuild_db.py has run. Say so
        # rather than letting the page 500 with nothing a reader can act on.
        return render_template("pages/1b_mission.html", db_missing=str(exc)), 503

    goals = _group_by_persona(db.query(db.load_query("persona_goals")), "goal")
    needs = _group_by_persona(db.query(db.load_query("persona_needs")), "need")
    pains = _group_by_persona(db.query(db.load_query("persona_pains")), "pain_point")
    attributes = _group_by_persona_and_category(
        db.query(db.load_query("persona_attributes")), ATTRIBUTE_CATEGORIES, "attribute")
    notes = _group_by_persona_and_category(
        db.query(db.load_query("persona_notes")), NOTE_CATEGORIES, "note")

    personas = []
    for p in persona_rows:
        pid = p["persona_id"]
        personas.append({
            "row": p,
            # The stylesheet targets #persona-grace / #persona-daniel by id
            # (only two personas exist), so the key is the first name, lowercased.
            "key": p["name"].split()[0].lower(),
            "goals": goals.get(pid, []),
            "needs": needs.get(pid, []),
            "pains": pains.get(pid, []),
            "personality": attributes[pid]["personality"],
            "profile": attributes[pid]["profile"],
            "source_used": attributes[pid]["source_used"],
            "trust_criterion": attributes[pid]["trust_criterion"],
            "motivation": attributes[pid]["motivation"],
            "tags": notes[pid]["tag"],
            "skill_tags": notes[pid]["skill_tag"],
            "behaviour": notes[pid]["behaviour"],
            "anti_goals": notes[pid]["anti_goal"],
        })

    return render_template(
        "pages/1b_mission.html",
        db_missing=None,
        team_members=team_members, team_photo=team_photo,
        personas=personas,
    )
