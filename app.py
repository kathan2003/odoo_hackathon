from __future__ import annotations

from pathlib import Path

from flask import Flask, render_template


# ---------------------------------------------------------
# APPLICATION CONFIGURATION
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

app.config["SECRET_KEY"] = "replace-this-with-a-secure-secret-key"

# Allows both /fuel and /fuel/, while url_for() generates /fuel.
app.url_map.strict_slashes = False


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@app.route("/")
def dashboard():
    dashboard_stats = {
        "total_vehicles": 48,
        "active_vehicles": 41,
        "drivers": 56,
        "available_drivers": 49,
        "fuel_cost": "₹17.82L",
        "fuel_change": "8.4% lower than last month",
        "fleet_utilization": "85.4%",
        "utilization_change": "+4.2% this month",
    }

    recent_trips = [
        {
            "vehicle": "GJ01AB1234",
            "driver": "Rohan Patel",
            "route": "Ahmedabad → Vadodara",
            "distance": "112 km",
            "status": "Completed",
        },
        {
            "vehicle": "GJ01CD5678",
            "driver": "Mehul Shah",
            "route": "Ahmedabad → Rajkot",
            "distance": "215 km",
            "status": "In Transit",
        },
        {
            "vehicle": "GJ05EF9012",
            "driver": "Nilesh Joshi",
            "route": "Surat → Bharuch",
            "distance": "76 km",
            "status": "Completed",
        },
        {
            "vehicle": "GJ18GH3456",
            "driver": "Amit Trivedi",
            "route": "Gandhinagar → Mehsana",
            "distance": "82 km",
            "status": "Scheduled",
        },
    ]

    return render_template(
        "dashboard.html",
        page_title="Dashboard",
        page_subtitle="Smart fleet management at a glance",
        stats=dashboard_stats,
        recent_trips=recent_trips,
    )


# ---------------------------------------------------------
# FUEL MANAGEMENT
# ---------------------------------------------------------

@app.route("/fuel")
def fuel():
    fuel_stats = {
        "total_used": "18,460 L",
        "fuel_cost": "₹17,82,400",
        "average_mileage": "12.8 km/L",
        "most_consuming_vehicle": "GJ01AB1234",
    }

    fuel_records = [
        {
            "date": "12 Jul 2026",
            "vehicle": "GJ01AB1234",
            "driver": "Rohan Patel",
            "fuel": "92 L",
            "cost": "₹8,740",
            "mileage": "11.4 km/L",
            "station": "IndianOil - SG Highway",
        },
        {
            "date": "11 Jul 2026",
            "vehicle": "GJ01CD5678",
            "driver": "Mehul Shah",
            "fuel": "76 L",
            "cost": "₹7,220",
            "mileage": "13.2 km/L",
            "station": "HP - Naroda",
        },
        {
            "date": "10 Jul 2026",
            "vehicle": "GJ05EF9012",
            "driver": "Nilesh Joshi",
            "fuel": "64 L",
            "cost": "₹6,080",
            "mileage": "14.1 km/L",
            "station": "BPCL - Surat",
        },
        {
            "date": "09 Jul 2026",
            "vehicle": "GJ18GH3456",
            "driver": "Amit Trivedi",
            "fuel": "58 L",
            "cost": "₹5,510",
            "mileage": "12.6 km/L",
            "station": "Shell - Gandhinagar",
        },
        {
            "date": "08 Jul 2026",
            "vehicle": "GJ27JK7890",
            "driver": "Krunal Desai",
            "fuel": "83 L",
            "cost": "₹7,890",
            "mileage": "10.9 km/L",
            "station": "Nayara - Changodar",
        },
    ]

    return render_template(
        "fuel.html",
        page_title="Fuel Management",
        page_subtitle="Monitor consumption, mileage and fuel spending",
        stats=fuel_stats,
        fuel_records=fuel_records,
    )


# ---------------------------------------------------------
# EXPENSE MANAGEMENT
# ---------------------------------------------------------

@app.route("/expense")
def expense():
    expense_stats = {
        "total": "₹24,86,500",
        "fuel": "₹17,82,400",
        "maintenance": "₹4,95,600",
        "other": "₹2,08,500",
    }

    expense_records = [
        {
            "date": "12 Jul 2026",
            "vehicle": "GJ01AB1234",
            "category": "Fuel",
            "description": "Diesel refill",
            "amount": "₹8,740",
            "payment": "Card",
            "status": "Completed",
        },
        {
            "date": "11 Jul 2026",
            "vehicle": "GJ01CD5678",
            "category": "Maintenance",
            "description": "Engine service",
            "amount": "₹45,000",
            "payment": "UPI",
            "status": "Pending",
        },
        {
            "date": "10 Jul 2026",
            "vehicle": "GJ05EF9012",
            "category": "Insurance",
            "description": "Annual insurance renewal",
            "amount": "₹32,500",
            "payment": "Bank Transfer",
            "status": "Completed",
        },
        {
            "date": "09 Jul 2026",
            "vehicle": "GJ18GH3456",
            "category": "Toll",
            "description": "FASTag recharge",
            "amount": "₹5,000",
            "payment": "UPI",
            "status": "Completed",
        },
        {
            "date": "08 Jul 2026",
            "vehicle": "GJ27JK7890",
            "category": "Maintenance",
            "description": "Tyre replacement",
            "amount": "₹28,400",
            "payment": "Card",
            "status": "Approved",
        },
    ]

    return render_template(
        "expenses.html",
        page_title="Expense Management",
        page_subtitle="Track, review and control fleet operating expenses",
        stats=expense_stats,
        expense_records=expense_records,
    )


# ---------------------------------------------------------
# REPORTS ANALYTICS
# ---------------------------------------------------------

@app.route("/reports")
def reports():
    report_stats = {
        "fuel_efficiency": "12.8 km/L",
        "operational_cost": "₹22.78L",
        "vehicle_roi": "31.6%",
        "fleet_utilization": "85.4%",
    }

    return render_template(
        "reports.html",
        page_title="Reports Analytics",
        page_subtitle="Actionable fleet insights and performance intelligence",
        stats=report_stats,
    )


# ---------------------------------------------------------
# VEHICLE MANAGEMENT
# ---------------------------------------------------------

@app.route("/vehicles")
def vehicles():
    return render_template(
        "module.html",
        page_title="Vehicles",
        page_subtitle="Vehicle registry and fleet availability",
        module_name="Vehicle Management",
        module_icon="bi-truck-front-fill",
        module_description=(
            "Add vehicles, monitor documents, assign drivers "
            "and track availability from this module."
        ),
    )


# ---------------------------------------------------------
# DRIVER MANAGEMENT
# ---------------------------------------------------------

@app.route("/drivers")
def drivers():
    return render_template(
        "module.html",
        page_title="Drivers",
        page_subtitle="Driver profiles, licences and availability",
        module_name="Driver Management",
        module_icon="bi-person-vcard-fill",
        module_description=(
            "Manage driver records, licence validity, attendance, "
            "assignments and performance."
        ),
    )


# ---------------------------------------------------------
# TRIP MANAGEMENT
# ---------------------------------------------------------

@app.route("/trips")
def trips():
    return render_template(
        "module.html",
        page_title="Trips",
        page_subtitle="Plan, dispatch and track fleet journeys",
        module_name="Trip Management",
        module_icon="bi-signpost-split-fill",
        module_description=(
            "Create trips, allocate vehicles and drivers, "
            "and monitor trip status and delivery progress."
        ),
    )


# ---------------------------------------------------------
# MAINTENANCE MANAGEMENT
# ---------------------------------------------------------

@app.route("/maintenance")
def maintenance():
    return render_template(
        "module.html",
        page_title="Maintenance",
        page_subtitle="Preventive service and repair management",
        module_name="Maintenance Management",
        module_icon="bi-tools",
        module_description=(
            "Schedule preventive maintenance, record repairs "
            "and receive service-due alerts."
        ),
    )


# ---------------------------------------------------------
# ERROR HANDLERS
# ---------------------------------------------------------

@app.errorhandler(404)
def page_not_found(error):
    return render_template(
        "module.html",
        page_title="Page Not Found",
        page_subtitle="The requested page could not be found",
        module_name="404 - Page Not Found",
        module_icon="bi-exclamation-triangle-fill",
        module_description=(
            "The page you requested does not exist. "
            "Please use the sidebar to navigate to another module."
        ),
    ), 404


# ---------------------------------------------------------
# START APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )