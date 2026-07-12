from flask import Flask, redirect, url_for, session

# Configuration
from config import Config

# Uncomment after creating database/db.py
# from database.db import db

# Blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.profile import profile_bp


def create_app():

    app = Flask(__name__)

    # Load Configuration
    app.config.from_object(Config)

    # ----------------------------
    # MySQL Connection
    # Uncomment after database setup
    # ----------------------------
    #
    # db.init_app(app)
    #
    # with app.app_context():
    #     db.create_all()
    #
    # ----------------------------

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(profile_bp)

    # Default Route
    @app.route("/")
    def home():

        # If user already logged in
        if session.get("user_id"):
            return redirect(url_for("dashboard.dashboard"))

        return redirect(url_for("auth.login"))

    # Logout
    @app.route("/logout")
    def logout():

        session.clear()

        return redirect(url_for("auth.login"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )