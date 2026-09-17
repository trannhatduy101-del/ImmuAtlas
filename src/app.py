"""
ImmuAtlas application factory.

This file registers blueprints and nothing else. Route logic lives in routes/,
one module per page, because two people work in this repository: if all six
routes lived here every change would collide, and the git history would not
show who wrote what. Both of those are graded (the project spec section 3 and 12).

Run:
    python run.py
"""

import os

from flask import Flask, render_template, url_for

import db

import config


def ensure_database():
    """Build the working database the first time the app starts without one.

    immuatlas.db is git-ignored, so a fresh clone or a downloaded ZIP arrives
    without it and every page answers 503 until someone runs rebuild_db.py.
    Nobody reads a README before pressing Run, so the app does that step itself.

    Deliberately not fatal. If the build fails -- immunisation2.db missing, no
    write permission, a syntax error in sql/ -- the app still starts, and
    db.connect() raises DatabaseMissing, which every page already turns into a
    503 naming the command to run. A failed build should leave a page that
    explains itself, not a traceback at import time.

    Cheap to call twice: `flask run --debug` builds the app in both the parent
    and the reloader child, and the second call finds the file and returns.
    """
    if os.path.exists(config.DB_PATH):
        return
    print("No working database found. Building it from immunisation2.db + sql/ ...")
    try:
        # Imported here, not at module scope, for the same reason as the
        # blueprints below: a failure names rebuild_db in the traceback.
        import rebuild_db
        rebuild_db.main()
    except Exception as exc:
        print("Automatic build failed (%s). Run: python src/rebuild_db.py" % exc)


def create_app():
    ensure_database()

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

    def static_v(filename):
        """url_for('static') plus ?v=<mtime>, so a changed file gets a new URL.

        Without it an edited stylesheet can keep serving from the browser cache
        even though Flask sends Cache-Control: no-cache -- the reader reloads,
        sees the old design, and reports the fix as not working. A version in
        the URL makes that impossible: a different file is a different address.

        Falls back to the plain URL if the file cannot be stat'd, so a missing
        asset is still a missing asset and never a 500.
        """
        try:
            stamp = int(os.stat(os.path.join(app.static_folder, filename)).st_mtime)
        except OSError:
            return url_for("static", filename=filename)
        return url_for("static", filename=filename, v=stamp)

    app.jinja_env.globals["static_v"] = static_v

    @app.context_processor
    def inject_shell():
        """Everything base.html needs, in one place.

        Deriving task / page_title / owner from ALL_PAGES means the nav bar and
        page heading can never disagree, and adding a page is a one-line change
        in routes/__init__.py rather than an edit in three files.
        """
        from flask import request
        from routes import PRIMARY_NAV, ALL_PAGES

        current = next((n for n in ALL_PAGES if n[0] == request.endpoint), None)

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


# `flask --app run run --debug` and run.py both pick this up.
app = create_app()


if __name__ == "__main__":
    # run.py at the repository root is the documented way in, but running this
    # file directly is a reflex, and without this block that command would build
    # the app and exit in silence -- which looks exactly like a crash with no
    # error message.
    app.run(debug=True)
