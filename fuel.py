from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import or_
from datetime import datetime

from database.models import db, FuelLog, Vehicle, Trip

fuel_bp = Blueprint("fuel", __name__, url_prefix="/fuel")


# ======================================================
# Fuel List Page
# ======================================================
@fuel_bp.route("/")
def fuel_page():

    vehicles = Vehicle.query.all()

    fuel_logs = FuelLog.query.order_by(
        FuelLog.fuel_date.desc()
    ).all()

    total_fuel = sum(log.fuel_liters for log in fuel_logs)

    total_cost = sum(log.fuel_cost for log in fuel_logs)

    average_price = (
        total_cost / total_fuel
        if total_fuel > 0
        else 0
    )

    return render_template(
        "fuel.html",
        vehicles=vehicles,
        fuel_logs=fuel_logs,
        total_fuel=round(total_fuel,2),
        total_cost=round(total_cost,2),
        average_price=round(average_price,2)
    )


# ======================================================
# Get Fuel Logs (AJAX)
# ======================================================
@fuel_bp.route("/api", methods=["GET"])
def get_fuel_logs():

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    search = request.args.get("search", "")
    vehicle = request.args.get("vehicle", "")

    query = FuelLog.query

    # -----------------------------
    # Search
    # -----------------------------

    if search:

        query = query.join(Vehicle).filter(
            or_(
                Vehicle.registration_number.ilike(f"%{search}%"),
                Vehicle.model.ilike(f"%{search}%"),
                FuelLog.fuel_station.ilike(f"%{search}%")
            )
        )

    # -----------------------------
    # Vehicle Filter
    # -----------------------------

    if vehicle:
        query = query.filter(FuelLog.vehicle_id == vehicle)

    query = query.order_by(FuelLog.fuel_date.desc())

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return jsonify({
        "success": True,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "data": [log.to_dict() for log in pagination.items]
    })


# ======================================================
# Add Fuel Log
# ======================================================
@fuel_bp.route("/add", methods=["POST"])
def add_fuel():

    data = request.get_json()

    vehicle_id = data.get("vehicle_id")
    trip_id = data.get("trip_id")
    fuel_liters = data.get("fuel_liters")
    fuel_cost = data.get("fuel_cost")
    fuel_station = data.get("fuel_station")
    fuel_date = data.get("fuel_date")

    # -----------------------------
    # Validation
    # -----------------------------

    if not vehicle_id:
        return jsonify({
            "success": False,
            "message": "Vehicle is required."
        }), 400

    if fuel_liters is None or float(fuel_liters) <= 0:
        return jsonify({
            "success": False,
            "message": "Fuel liters must be greater than zero."
        }), 400

    if fuel_cost is None or float(fuel_cost) <= 0:
        return jsonify({
            "success": False,
            "message": "Fuel cost must be greater than zero."
        }), 400

    try:
        fuel_date = datetime.strptime(
            fuel_date,
            "%Y-%m-%d"
        ).date()
    except:
        return jsonify({
            "success": False,
            "message": "Invalid date."
        }), 400

    fuel = FuelLog(
        vehicle_id=vehicle_id,
        trip_id=trip_id,
        fuel_liters=fuel_liters,
        fuel_cost=fuel_cost,
        fuel_station=fuel_station,
        fuel_date=fuel_date
    )

    db.session.add(fuel)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Fuel log added successfully."
    })


# ======================================================
# Update Fuel
# ======================================================
@fuel_bp.route("/update/<int:id>", methods=["PUT"])
def update_fuel(id):

    fuel = FuelLog.query.get_or_404(id)

    data = request.get_json()

    fuel.vehicle_id = data["vehicle_id"]
    fuel.trip_id = data.get("trip_id")
    fuel.fuel_liters = data["fuel_liters"]
    fuel.fuel_cost = data["fuel_cost"]
    fuel.fuel_station = data.get("fuel_station")
    fuel.fuel_date = datetime.strptime(
        data["fuel_date"],
        "%Y-%m-%d"
    ).date()

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Fuel log updated successfully."
    })


# ======================================================
# Delete Fuel
# ======================================================
@fuel_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_fuel(id):

    fuel = FuelLog.query.get_or_404(id)

    db.session.delete(fuel)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Fuel log deleted."
    })


# ======================================================
# Get Vehicles Dropdown
# ======================================================
@fuel_bp.route("/vehicles")
def vehicles():

    vehicles = Vehicle.query.filter(
        Vehicle.status != "Retired"
    ).all()

    return jsonify([
        {
            "id": vehicle.id,
            "registration": vehicle.registration_number,
            "model": vehicle.model
        }
        for vehicle in vehicles
    ])


# ======================================================
# Get Trips Dropdown
# ======================================================
@fuel_bp.route("/trips")
def trips():

    trips = Trip.query.all()

    return jsonify([
        {
            "id": trip.id,
            "source": trip.source,
            "destination": trip.destination
        }
        for trip in trips
    ])