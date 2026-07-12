from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash

# Uncomment when using MySQL
"""
from database.db import db
from database.models import Vehicle
"""

vehicle_bp = Blueprint("vehicle", __name__)

# Temporary storage (works without MySQL)
vehicles_data = []


# ===========================
# View All Vehicles
# ===========================
@vehicle_bp.route("/")
@vehicle_bp.route("/vehicles")
def vehicles():

    search = request.args.get("search", "").lower()

    if search:

        vehicle_list = [
            vehicle for vehicle in vehicles_data
            if search in vehicle["registration_number"].lower()
        ]

    else:

        vehicle_list = vehicles_data

    return render_template(
        "vehicles.html",
        vehicles=vehicle_list
    )


# ===========================
# Add Vehicle
# ===========================
@vehicle_bp.route("/vehicles/add", methods=["GET", "POST"])
def add_vehicle():

    if request.method == "POST":

        print("POST request received!")

        registration_number = request.form["registration_number"]

        # Check duplicate registration number
        for vehicle in vehicles_data:

            if vehicle["registration_number"] == registration_number:

                flash("Vehicle already exists!", "danger")
                return redirect(url_for("vehicle.add_vehicle"))

        new_vehicle = {

            "id": len(vehicles_data) + 1,

            "registration_number": registration_number,

            "model": request.form["model"],

            "vehicle_type": request.form["vehicle_type"],

            "capacity": request.form["capacity"],

            "odometer": request.form["odometer"],

            "acquisition_cost": request.form["acquisition_cost"],

            "status": request.form["status"]

        }

        vehicles_data.append(new_vehicle)

        flash("Vehicle Added Successfully!", "success")

        return redirect(url_for("vehicle.vehicles"))

    return render_template("vehicle_add.html")


# ===========================
# MySQL Version
# Uncomment Later
# ===========================

"""
from database.db import db
from database.models import Vehicle

@vehicle_bp.route("/vehicles/add", methods=["GET", "POST"])
def add_vehicle():

    if request.method == "POST":

        vehicle = Vehicle(

            registration_number=request.form["registration_number"],

            model=request.form["model"],

            vehicle_type=request.form["vehicle_type"],

            capacity=request.form["capacity"],

            odometer=request.form["odometer"],

            acquisition_cost=request.form["acquisition_cost"],

            status=request.form["status"]

        )

        db.session.add(vehicle)
        db.session.commit()

        flash("Vehicle Added Successfully!", "success")

        return redirect(url_for("vehicle.vehicles"))

    return render_template("vehicle_add.html")
"""