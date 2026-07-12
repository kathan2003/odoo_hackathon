from flask import Blueprint, render_template, request, redirect, url_for

trip_bp = Blueprint("trip", __name__)

# -----------------------------
# Temporary Mock Database
# -----------------------------

trips = [
    {
        "id": "TRP001",
        "source": "Ahmedabad",
        "destination": "Surat",
        "vehicle": "Van-05",
        "driver": "Alex",
        "cargo": "450 Kg",
        "distance": "270 KM",
        "status": "Draft"
    },
    {
        "id": "TRP002",
        "source": "Rajkot",
        "destination": "Vadodara",
        "vehicle": "Truck-11",
        "driver": "John",
        "cargo": "700 Kg",
        "distance": "340 KM",
        "status": "Dispatched"
    },
    {
        "id": "TRP003",
        "source": "Bhavnagar",
        "destination": "Ahmedabad",
        "vehicle": "Mini Van",
        "driver": "Mike",
        "cargo": "300 Kg",
        "distance": "180 KM",
        "status": "Completed"
    }
]


# -----------------------------
# Trip List
# -----------------------------

@trip_bp.route("/trips")
def trip_list():
    return render_template(
        "trip/trip_list.html",
        trips=trips
    )


# -----------------------------
# Create Trip Page
# -----------------------------

@trip_bp.route("/trip/create")
def create_trip():
    return render_template(
        "trip/create_trip.html"
    )


# -----------------------------
# Save New Trip
# -----------------------------

@trip_bp.route("/trip/create", methods=["POST"])
def save_trip():

    new_trip = {

        "id": request.form["trip_id"],

        "source": request.form["source"],

        "destination": request.form["destination"],

        "vehicle": request.form["vehicle"],

        "driver": request.form["driver"],

        "cargo": request.form["cargo"],

        "distance": request.form["distance"],

        "status": "Draft"

    }

    trips.append(new_trip)

    return redirect(url_for("trip.trip_list"))


# -----------------------------
# Trip Details
# -----------------------------

@trip_bp.route("/trip/details/<trip_id>")
def trip_details(trip_id):

    trip = next(

        (t for t in trips if t["id"] == trip_id),

        None

    )

    return render_template(

        "trip/trip_details.html",

        trip=trip

    )


# -----------------------------
# Dispatch
# -----------------------------

@trip_bp.route("/trip/dispatch/<trip_id>")

def dispatch_trip(trip_id):

    for trip in trips:

        if trip["id"] == trip_id:

            trip["status"] = "Dispatched"

            break

    return redirect(url_for("trip.trip_list"))


# -----------------------------
# Complete
# -----------------------------

@trip_bp.route("/trip/complete/<trip_id>")

def complete_trip(trip_id):

    for trip in trips:

        if trip["id"] == trip_id:

            trip["status"] = "Completed"

            break

    return redirect(url_for("trip.trip_list"))


# -----------------------------
# Cancel
# -----------------------------

@trip_bp.route("/trip/cancel/<trip_id>")

def cancel_trip(trip_id):

    for trip in trips:

        if trip["id"] == trip_id:

            trip["status"] = "Cancelled"

            break

    return redirect(url_for("trip.trip_list"))