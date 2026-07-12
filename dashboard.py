from flask import Blueprint, render_template, session, redirect, url_for

dashboard_bp = Blueprint("dashboard", __name__)


# ==========================================
# Dashboard
# ==========================================

@dashboard_bp.route("/dashboard")
def dashboard():

    # Check Login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Dashboard Data
    user = {
        "name": session.get("user_name"),
        "role": session.get("role")
    }

    # Sample Dashboard Statistics
    dashboard_data = {

        "total_vehicles": 42,
        "active_vehicles": 30,
        "maintenance": 5,
        "drivers": 28,
        "active_trips": 18,
        "fleet_utilization": "72%"
    }

    return render_template(
        "dashboard.html",
        user=user,
        data=dashboard_data
    )