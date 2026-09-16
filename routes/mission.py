"""1B Mission statement -- Sub-Task B.

Brief 1B requires personas and team members to be stored in and retrieved
from the database. Team members were already DB-driven; this route reads
the full persona model (persona + its five child tables) instead of the
Python constant that used to hold the copy.
"""

from collections import defaultdict

from flask import Blueprint, render_template

import db

bp = Blueprint("mission", __name__)

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
        # A fresh clone has no immuatlas.db until rebuild_db.sh has run. Say so
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
        team_members=team_members,
        personas=personas,
    )
