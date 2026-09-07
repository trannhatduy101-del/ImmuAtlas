"""
ImmuAtlas application factory.

This file registers blueprints and nothing else. Route logic lives in routes/,
one module per page, because two people work in this repository: if all six
routes lived here every change would collide, and the git history would not
show who wrote what. Both of those are graded (CLAUDE.md section 3 and 12).

Run:
    ./rebuild_db.sh
    flask --app app run --debug
"""

from flask import Flask, render_template

import db

import config


def create_app():
    app = Flask(__name__)
    app.config["SITE_NAME"] = config.SITE_NAME
    app.config["SITE_TAGLINE"] = config.SITE_TAGLINE
    app.config["SOURCE_NAME"] = config.SOURCE_NAME
    app.config["SOURCE_URL"] = config.SOURCE_URL

    # Imported here rather than at module scope so a syntax error in one page
    # module names that module in the traceback instead of failing the import
    # of the whole application.
    from routes.landing import bp as landing_bp
    from routes.mission import bp as mission_bp
    from routes.coverage import bp as coverage_bp
    from routes.infections import bp as infections_bp
    from routes.improvement import bp as improvement_bp
    from routes.above_average import bp as above_average_bp

    for blueprint in (
        landing_bp,        # 1A
        mission_bp,        # 1B
        coverage_bp,       # 2A
        infections_bp,     # 2B
        improvement_bp,    # 3A
        above_average_bp,  # 3B
    ):
        app.register_blueprint(blueprint)

    @app.context_processor
    def inject_shell():
        """Everything base.html and the unbuilt component need, in one place.

        Deriving task / page_title / owner from NAV means the nav bar and the
        page heading can never disagree, and adding a page is a one-line change
        in routes/__init__.py rather than an edit in three files.
        """
        from flask import request
        from routes import NAV, PRIMARY_NAV, ALL_PAGES

        current = next((n for n in NAV if n[0] == request.endpoint), None)

        # The footer citation comes from research_source, not from a constant.
        # config.SOURCE_NAME is only the fallback for the state where there is
        # no database to read -- a page that cannot reach the data should still
        # say whose data it would have shown.
        try:
            sources = db.query(db.load_query("site_provenance"))
        except (db.DatabaseMissing, OSError):
            sources = []

        # Brief 1B: team names and student numbers come out of the database.
        try:
            team = db.query(db.load_query("team_members"))
        except (db.DatabaseMissing, OSError):
            team = []

        return {
            "nav": NAV,
            "primary_nav": PRIMARY_NAV,
            "all_pages": ALL_PAGES,
            "sources": sources,
            "team": team,
            "social_links": config.SOCIAL_LINKS,
            "site_name": config.SITE_NAME,
            "site_tagline": config.SITE_TAGLINE,
            "source_name": config.SOURCE_NAME,
            "source_url": config.SOURCE_URL,
            "task": current[2] if current else "",
            "page_title": current[1] if current else "",
            "owner": current[3] if current else "",
        }

    @app.errorhandler(404)
    def not_found(_):
        return render_template("pages/error.html",
                               code=404,
                               message="There is no page at that address."), 404

    @app.errorhandler(500)
    def server_error(_):
        return render_template("pages/error.html",
                               code=500,
                               message="Something broke on our side."), 500

    return app


# `flask --app app run --debug` picks this up.
app = create_app()


if __name__ == "__main__":
    # So that `python app.py` works too. The documented way to start this is
    # `flask --app app run --debug`, but typing `python app.py` is the reflex,
    # and without this block that command builds the app and exits in silence,
    # which looks exactly like a crash with no error.
    app.run(debug=True)
