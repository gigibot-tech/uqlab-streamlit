"""Lean Flask UI for uqlab uncertainty experiments."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
FLASK_PKG = Path(__file__).resolve().parent
for p in (str(SRC), str(ROOT), str(FLASK_PKG)):
    if p not in sys.path:
        sys.path.insert(0, p)

from flask import Flask

from uqlab_flask.routes.runs import bp as runs_bp
from uqlab_flask.routes.wizard import bp as wizard_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(FLASK_PKG / "uqlab_flask" / "templates"),
        static_folder=str(FLASK_PKG / "uqlab_flask" / "static"),
    )
    app.secret_key = "uqlab-dev-change-in-production"
    app.config["PROJECT_ROOT"] = ROOT
    app.config["EXPERIMENTS_DIR"] = ROOT / "data" / "experiments"
    app.register_blueprint(wizard_bp)
    app.register_blueprint(runs_bp, url_prefix="/api")
    return app


if __name__ == "__main__":
    # use_reloader=False — watchdog reload kills in-flight training threads mid-sweep.
    create_app().run(debug=True, use_reloader=False, port=5001)
