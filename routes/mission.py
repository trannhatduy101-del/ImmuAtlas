"""1B Mission statement -- Sub-Task B."""

from flask import Blueprint, render_template

import db

bp = Blueprint("mission", __name__)

# Persona content transcribed from the project's persona brief. Each personality
# trait carries a 0-100 position (left label -> right label); motivations and
# channels carry a 0-100 bar length, matching the persona sheets.
PERSONAS = [
    {
        "key": "grace",
        "name": "Grace Achieng",
        "photo": "img/grace-photo.png",
        "age": "41 years old",
        "location": "Kisumu, Kenya",
        "occupation": "Health Promotion and Immunisation Officer",
        "group": "Health Communicators",
        "quote": "I need one number I can defend in a room, and I need to know "
                 "how it was calculated before I put my name next to it.",
        "bio": "Grace manages immunisation communication and reporting for a "
               "county health office in Kisumu, Kenya. She relies on credible "
               "data to explain performance and support public-health decisions, "
               "and needs figures that are transparent, well-supported and easy "
               "to defend.",
        "personality": [
            {"left": "Analytical", "right": "Intuitive", "pos": 22},
            {"left": "Cautious", "right": "Risk-taking", "pos": 58},
            {"left": "Independent", "right": "Team-oriented", "pos": 28},
            {"left": "Methodical", "right": "Spontaneous", "pos": 42},
            {"left": "Accountable", "right": "Flexible", "pos": 35},
        ],
        "skills": [
            "14 years of experience in immunisation programmes.",
            "Confident interpreting coverage rates, denominators and time series.",
            "Experienced with Excel but does not use SQL or Python.",
        ],
        "goals": [
            "Identify countries and regions with the greatest vaccination improvements.",
            "Confirm figures and calculations before presenting them to decision-makers.",
        ],
        "needs": [
            "Visible calculation methods, stated denominators and published limitations.",
            "Clear benchmarks, ranked results and citations attached to every figure.",
        ],
        "pains": [
            "Cannot confidently use a figure when its calculation method is unclear.",
            "Imperfect or missing data can make reported improvements difficult to trust.",
        ],
        "motivations": [
            {"label": "Time Efficiency", "pct": 72},
            {"label": "Public Health Impact", "pct": 40},
            {"label": "Professional Accountability", "pct": 16},
            {"label": "Credible Communication", "pct": 90},
            {"label": "Evidence-Based Decisions", "pct": 20},
        ],
        "channels": [
            {"label": "Data Dashboards", "pct": 75},
            {"label": "Professional Email", "pct": 68},
            {"label": "Social Media", "pct": 30},
            {"label": "Research & Reports", "pct": 16},
            {"label": "Official Health Websites", "pct": 12},
        ],
    },
    {
        "key": "daniel",
        "name": "Daniel Nguyen",
        "photo": "img/daniel-photo.png",
        "age": "46 years old",
        "location": "Melbourne, Australia",
        "occupation": "Operations Coordinator",
        "group": "General Public",
        "quote": "I don't need to be a health expert. I just want enough reliable "
                 "evidence to understand what the numbers actually mean.",
        "bio": "Daniel is interested in understanding vaccination and "
               "preventable-disease trends. He checks reliable evidence and "
               "compares information before forming his own opinion, and prefers "
               "trustworthy sources with clear explanations of health data.",
        "personality": [
            {"left": "Analytical", "right": "Intuitive", "pos": 20},
            {"left": "Cautious", "right": "Risk-taking", "pos": 52},
            {"left": "Independent", "right": "Team-oriented", "pos": 35},
            {"left": "Patient", "right": "Impatient", "pos": 55},
            {"left": "Fact-driven", "right": "Emotion-driven", "pos": 30},
        ],
        "skills": [
            "Comfortable using websites and search engines.",
            "Understands basic rates, percentages and comparisons.",
            "Can evaluate information from different sources.",
        ],
        "goals": [
            "Understand how vaccination and infection rates change over time.",
            "Compare countries and economic groups using reliable evidence.",
        ],
        "needs": [
            "Reliable evidence with clear context about countries, years and rates.",
            "Easy comparison and independent exploration to answer his own questions.",
        ],
        "pains": [
            "Health statistics can be difficult to interpret without context.",
            "Online health information can vary in reliability.",
        ],
        "motivations": [
            {"label": "Helping Family & Community", "pct": 72},
            {"label": "Personal Curiosity", "pct": 68},
            {"label": "Staying Updated", "pct": 40},
            {"label": "Making Informed Decisions", "pct": 30},
            {"label": "Understanding & Learning", "pct": 15},
        ],
        "channels": [
            {"label": "News & Online Articles", "pct": 72},
            {"label": "Email Newsletters", "pct": 68},
            {"label": "Social Media", "pct": 45},
            {"label": "Search Engines", "pct": 20},
            {"label": "Websites", "pct": 10},
        ],
    },
]


@bp.route("/mission")
def index():
    team_members = db.query(db.load_query("team_members"))
    return render_template(
        "pages/1b_mission.html",
        team_members=team_members,
        personas=PERSONAS,
    )
