import io
from datetime import datetime

import pandas as pd
from flask import (
    Blueprint,
    render_template,
    jsonify,
    Response
)

from sqlalchemy import func

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from database.db import db
from database.models import (
    Vehicle,
    Trip,
    FuelLog,
    Expense
)

reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports"
)


# ============================================================
# Dashboard
# ============================================================

@reports_bp.route("/")
def dashboard():

    total_vehicles = Vehicle.query.count()

    available_vehicles = Vehicle.query.filter_by(
        status="Available"
    ).count()

    on_trip = Vehicle.query.filter_by(
        status="On Trip"
    ).count()

    retired = Vehicle.query.filter_by(
        status="Retired"
    ).count()

    total_expense = db.session.query(
        func.sum(Expense.amount)
    ).scalar() or 0

    total_fuel_cost = db.session.query(
        func.sum(FuelLog.fuel_cost)
    ).scalar() or 0

    maintenance_cost = db.session.query(
        func.sum(Expense.amount)
    ).filter(
        Expense.expense_type == "Maintenance"
    ).scalar() or 0

    operational_cost = (
        total_fuel_cost +
        maintenance_cost
    )

    fleet_utilization = 0

    if total_vehicles > 0:

        fleet_utilization = round(
            (on_trip / total_vehicles) * 100,
            2
        )

    dashboard_data = {

        "total_vehicles": total_vehicles,

        "available_vehicles": available_vehicles,

        "on_trip": on_trip,

        "retired": retired,

        "fleet_utilization": fleet_utilization,

        "total_fuel_cost": round(
            total_fuel_cost,
            2
        ),

        "maintenance_cost": round(
            maintenance_cost,
            2
        ),

        "operational_cost": round(
            operational_cost,
            2
        ),

        "total_expense": round(
            total_expense,
            2
        )
    }

    return render_template(
        "reports.html",
        dashboard=dashboard_data
    )


# ============================================================
# Vehicle Analytics
# ============================================================

@reports_bp.route("/analytics")
def analytics():

    vehicles = Vehicle.query.all()

    report_data = []

    for vehicle in vehicles:

        trips = Trip.query.filter_by(
            vehicle_id=vehicle.id
        ).all()

        fuel_logs = FuelLog.query.filter_by(
            vehicle_id=vehicle.id
        ).all()

        expenses = Expense.query.filter_by(
            vehicle_id=vehicle.id
        ).all()

        # --------------------------
        # Distance
        # --------------------------

        total_distance = sum(
            trip.distance
            for trip in trips
        )

        # --------------------------
        # Revenue
        # --------------------------

        total_revenue = sum(
            trip.revenue
            for trip in trips
        )

        # --------------------------
        # Fuel
        # --------------------------

        fuel_used = sum(
            log.fuel_liters
            for log in fuel_logs
        )

        fuel_cost = sum(
            log.fuel_cost
            for log in fuel_logs
        )

        # --------------------------
        # Maintenance
        # --------------------------

        maintenance_cost = sum(

            expense.amount

            for expense in expenses

            if expense.expense_type == "Maintenance"

        )

        # --------------------------
        # Other Expenses
        # --------------------------

        other_expense = sum(

            expense.amount

            for expense in expenses

            if expense.expense_type != "Maintenance"

        )

        # --------------------------
        # Fuel Efficiency
        # --------------------------

        efficiency = 0

        if fuel_used > 0:

            efficiency = round(

                total_distance /

                fuel_used,

                2

            )

        # --------------------------
        # Operational Cost
        # --------------------------

        operational_cost = (

            fuel_cost +

            maintenance_cost +

            other_expense

        )

        # --------------------------
        # ROI
        # --------------------------

        roi = 0

        if vehicle.acquisition_cost > 0:

            roi = round(

                (

                    total_revenue -

                    operational_cost

                )

                /

                vehicle.acquisition_cost

                * 100,

                2

            )

        report_data.append({

            "vehicle": vehicle.registration_number,

            "model": vehicle.model,

            "distance": total_distance,

            "fuel_used": fuel_used,

            "fuel_cost": fuel_cost,

            "maintenance": maintenance_cost,

            "other_expense": other_expense,

            "operational_cost": operational_cost,

            "fuel_efficiency": efficiency,

            "revenue": total_revenue,

            "roi": roi

        })

    return jsonify(report_data)
# ============================================================
# Dashboard Summary API
# ============================================================

@reports_bp.route("/summary")
def dashboard_summary():

    total_vehicles = Vehicle.query.count()

    available = Vehicle.query.filter_by(
        status="Available"
    ).count()

    on_trip = Vehicle.query.filter_by(
        status="On Trip"
    ).count()

    retired = Vehicle.query.filter_by(
        status="Retired"
    ).count()

    fuel_cost = db.session.query(
        func.sum(FuelLog.fuel_cost)
    ).scalar() or 0

    total_expense = db.session.query(
        func.sum(Expense.amount)
    ).scalar() or 0

    maintenance = db.session.query(
        func.sum(Expense.amount)
    ).filter(
        Expense.expense_type == "Maintenance"
    ).scalar() or 0

    operational = fuel_cost + maintenance

    utilization = 0

    if total_vehicles > 0:
        utilization = round(
            (on_trip / total_vehicles) * 100,
            2
        )

    return jsonify({

        "vehicles": total_vehicles,

        "available": available,

        "on_trip": on_trip,

        "retired": retired,

        "fuel_cost": round(fuel_cost, 2),

        "maintenance": round(maintenance, 2),

        "operational_cost": round(operational, 2),

        "total_expense": round(total_expense, 2),

        "fleet_utilization": utilization

    })


# ============================================================
# Fuel Cost Chart
# ============================================================

@reports_bp.route("/chart/fuel-cost")
def fuel_cost_chart():

    vehicles = Vehicle.query.all()

    labels = []
    values = []

    for vehicle in vehicles:

        total = db.session.query(
            func.sum(FuelLog.fuel_cost)
        ).filter(
            FuelLog.vehicle_id == vehicle.id
        ).scalar() or 0

        labels.append(vehicle.registration_number)

        values.append(round(total, 2))

    return jsonify({

        "labels": labels,

        "values": values

    })


# ============================================================
# Expense Breakdown Chart
# ============================================================

@reports_bp.route("/chart/expense-breakdown")
def expense_breakdown():

    data = db.session.query(

        Expense.expense_type,

        func.sum(Expense.amount)

    ).group_by(

        Expense.expense_type

    ).all()

    labels = []

    values = []

    for item in data:

        labels.append(item[0])

        values.append(float(item[1]))

    return jsonify({

        "labels": labels,

        "values": values

    })


# ============================================================
# Fleet Utilization Chart
# ============================================================

@reports_bp.route("/chart/utilization")
def utilization_chart():

    available = Vehicle.query.filter_by(
        status="Available"
    ).count()

    trip = Vehicle.query.filter_by(
        status="On Trip"
    ).count()

    shop = Vehicle.query.filter_by(
        status="In Shop"
    ).count()

    retired = Vehicle.query.filter_by(
        status="Retired"
    ).count()

    return jsonify({

        "labels": [

            "Available",

            "On Trip",

            "In Shop",

            "Retired"

        ],

        "values": [

            available,

            trip,

            shop,

            retired

        ]

    })


# ============================================================
# ROI Chart
# ============================================================

@reports_bp.route("/chart/roi")
def roi_chart():

    labels = []

    values = []

    vehicles = Vehicle.query.all()

    for vehicle in vehicles:

        trips = Trip.query.filter_by(
            vehicle_id=vehicle.id
        ).all()

        revenue = sum(
            trip.revenue
            for trip in trips
        )

        fuel = db.session.query(
            func.sum(FuelLog.fuel_cost)
        ).filter(
            FuelLog.vehicle_id == vehicle.id
        ).scalar() or 0

        maintenance = db.session.query(
            func.sum(Expense.amount)
        ).filter(
            Expense.vehicle_id == vehicle.id,
            Expense.expense_type == "Maintenance"
        ).scalar() or 0

        roi = 0

        if vehicle.acquisition_cost > 0:

            roi = (

                (

                    revenue -

                    (fuel + maintenance)

                )

                /

                vehicle.acquisition_cost

            ) * 100

        labels.append(

            vehicle.registration_number

        )

        values.append(

            round(roi, 2)

        )

    return jsonify({

        "labels": labels,

        "values": values

    })


# ============================================================
# Monthly Fuel Trend
# ============================================================

@reports_bp.route("/chart/fuel-trend")
def fuel_trend():

    logs = FuelLog.query.order_by(
        FuelLog.fuel_date.asc()
    ).all()

    labels = []

    values = []

    for log in logs:

        labels.append(

            log.fuel_date.strftime("%b %Y")

        )

        values.append(

            log.fuel_cost

        )

    return jsonify({

        "labels": labels,

        "values": values

    })
# ============================================================
# Export Expenses to CSV
# ============================================================

@reports_bp.route("/export/csv")
def export_csv():

    expenses = Expense.query.order_by(
        Expense.expense_date.desc()
    ).all()

    data = []

    for expense in expenses:

        vehicle = Vehicle.query.get(expense.vehicle_id)

        data.append({

            "Vehicle": vehicle.registration_number if vehicle else "N/A",

            "Expense Type": expense.expense_type,

            "Amount": expense.amount,

            "Expense Date": expense.expense_date,

            "Description": expense.description

        })

    df = pd.DataFrame(data)

    output = io.StringIO()

    df.to_csv(output, index=False)

    csv_data = output.getvalue()

    output.close()

    return Response(

        csv_data,

        mimetype="text/csv",

        headers={

            "Content-Disposition":

            "attachment; filename=TransitOps_Report.csv"

        }

    )


# ============================================================
# Export Analytics PDF
# ============================================================

@reports_bp.route("/export/pdf")
def export_pdf():

    buffer = io.BytesIO()

    pdf = canvas.Canvas(

        buffer,

        pagesize=letter

    )

    pdf.setTitle("TransitOps Report")

    pdf.setFont("Helvetica-Bold", 18)

    pdf.drawString(

        170,

        780,

        "TransitOps Analytics Report"

    )

    pdf.setFont(

        "Helvetica",

        11

    )

    y = 740

    vehicles = Vehicle.query.all()

    for vehicle in vehicles:

        trips = Trip.query.filter_by(

            vehicle_id=vehicle.id

        ).all()

        logs = FuelLog.query.filter_by(

            vehicle_id=vehicle.id

        ).all()

        expenses = Expense.query.filter_by(

            vehicle_id=vehicle.id

        ).all()

        distance = sum(

            t.distance

            for t in trips

        )

        revenue = sum(

            t.revenue

            for t in trips

        )

        fuel = sum(

            f.fuel_liters

            for f in logs

        )

        fuel_cost = sum(

            f.fuel_cost

            for f in logs

        )

        expense_cost = sum(

            e.amount

            for e in expenses

        )

        efficiency = 0

        if fuel > 0:

            efficiency = round(

                distance /

                fuel,

                2

            )

        roi = 0

        if vehicle.acquisition_cost > 0:

            roi = round(

                (

                    revenue -

                    expense_cost -

                    fuel_cost

                )

                /

                vehicle.acquisition_cost

                * 100,

                2

            )

        pdf.drawString(

            40,

            y,

            f"Vehicle : {vehicle.registration_number}"

        )

        y -= 15

        pdf.drawString(

            60,

            y,

            f"Distance : {distance} km"

        )

        y -= 15

        pdf.drawString(

            60,

            y,

            f"Fuel Used : {fuel:.2f} L"

        )

        y -= 15

        pdf.drawString(

            60,

            y,

            f"Fuel Cost : ₹ {fuel_cost:.2f}"

        )

        y -= 15

        pdf.drawString(

            60,

            y,

            f"Operational Cost : ₹ {expense_cost + fuel_cost:.2f}"

        )

        y -= 15

        pdf.drawString(

            60,

            y,

            f"Fuel Efficiency : {efficiency:.2f} km/L"

        )

        y -= 15

        pdf.drawString(

            60,

            y,

            f"ROI : {roi:.2f}%"

        )

        y -= 25

        if y < 80:

            pdf.showPage()

            pdf.setFont(

                "Helvetica",

                11

            )

            y = 760

    pdf.save()

    buffer.seek(0)

    return Response(

        buffer,

        mimetype="application/pdf",

        headers={

            "Content-Disposition":

            "attachment; filename=TransitOps_Report.pdf"

        }

    )


# ============================================================
# Complete Report JSON API
# ============================================================

@reports_bp.route("/api")
def report_api():

    vehicles = Vehicle.query.all()

    reports = []

    for vehicle in vehicles:

        trips = Trip.query.filter_by(

            vehicle_id=vehicle.id

        ).all()

        logs = FuelLog.query.filter_by(

            vehicle_id=vehicle.id

        ).all()

        expenses = Expense.query.filter_by(

            vehicle_id=vehicle.id

        ).all()

        distance = sum(

            t.distance

            for t in trips

        )

        revenue = sum(

            t.revenue

            for t in trips

        )

        fuel_used = sum(

            f.fuel_liters

            for f in logs

        )

        fuel_cost = sum(

            f.fuel_cost

            for f in logs

        )

        expense = sum(

            e.amount

            for e in expenses

        )

        efficiency = 0

        if fuel_used > 0:

            efficiency = round(

                distance /

                fuel_used,

                2

            )

        roi = 0

        if vehicle.acquisition_cost > 0:

            roi = round(

                (

                    revenue -

                    expense -

                    fuel_cost

                )

                /

                vehicle.acquisition_cost

                * 100,

                2

            )

        reports.append({

            "vehicle":

                vehicle.registration_number,

            "distance":

                distance,

            "fuel_used":

                fuel_used,

            "fuel_cost":

                fuel_cost,

            "expenses":

                expense,

            "fuel_efficiency":

                efficiency,

            "roi":

                roi

        })

    return jsonify(reports)