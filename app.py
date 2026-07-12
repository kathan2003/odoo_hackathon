import os
from flask import Flask, render_template
from database.db import db

# Import Blueprints
from routes.fuel import fuel_bp
from routes.expense import expense_bp
from routes.reports import reports_bp


def create_app():
    app = Flask(
    __name__,
    template_folder="template",
    static_folder="static"
)
    # ----------------------------------------------------
    # Basic Configuration
    # ----------------------------------------------------
    app.config['SECRET_KEY'] = 'transitops-super-secret-key'

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # SQLite (Local Development)
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        f"sqlite:///{os.path.join(BASE_DIR, 'transitops.db')}"

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ----------------------------------------------------
    # Initialize Database
    # ----------------------------------------------------
    db.init_app(app)

    # ----------------------------------------------------
    # Create Database Tables
    # ----------------------------------------------------
    with app.app_context():
        from database.models import (
            User,
            Vehicle,
            Trip,
            FuelLog,
            Expense
        )

        db.create_all()

    # ----------------------------------------------------
    # Register Blueprints
    # ----------------------------------------------------
    app.register_blueprint(fuel_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(reports_bp)

    # ----------------------------------------------------
    # Home
    # ----------------------------------------------------
    @app.route("/")
    def home():
        return render_template("base.html")

    # ----------------------------------------------------
    # Health Check
    # ----------------------------------------------------
    @app.route("/health")
    def health():
        return {
            "status": "running",
            "application": "TransitOps",
            "module": "Reports & Analytics"
        }

    # ----------------------------------------------------
    # Error Pages
    # ----------------------------------------------------
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template("500.html"), 500

    return app


# ----------------------------------------------------
# Run Application
# ----------------------------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )