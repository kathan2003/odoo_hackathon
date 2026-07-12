from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash

# Uncomment when using MySQL
"""
from database.db import db
from database.models import Driver
"""

driver_bp = Blueprint("driver", __name__)

# Temporary storage (works without MySQL)
drivers_data = []


# ===========================
# View All Drivers
# ===========================
@driver_bp.route("/drivers")
@driver_bp.route("/drivers/")
def drivers():

    search = request.args.get("search", "").lower()

    if search:

        driver_list = [
            driver for driver in drivers_data
            if search in driver["name"].lower()
            or search in driver["license_number"].lower()
        ]

    else:

        driver_list = drivers_data

    return render_template(
        "drivers.html",
        drivers=driver_list
    )


# ===========================
# Add Driver
# ===========================
@driver_bp.route("/drivers/add", methods=["GET", "POST"])
@driver_bp.route("/drivers/add/", methods=["GET", "POST"])
def add_driver():

    if request.method == "POST":

        license_number = request.form["license_number"]

        # Check duplicate license number
        for driver in drivers_data:

            if driver["license_number"] == license_number:

                flash("Driver already exists!", "danger")

                return redirect(
                    url_for("driver.add_driver")
                )

        new_driver = {

            "id": len(drivers_data) + 1,

            "name": request.form["name"],

            "license_number": license_number,

            "phone": request.form["phone"],

            "experience": request.form["experience"],

            "status": request.form["status"]

        }

        drivers_data.append(new_driver)

        flash(
            "Driver Added Successfully!",
            "success"
        )

        return redirect(
            url_for("driver.drivers")
        )

    return render_template(
        "driver_add.html"
    )


# ===========================
# MySQL Version
# Uncomment Later
# ===========================

"""
from database.db import db
from database.models import Driver

@driver_bp.route("/drivers/add", methods=["GET", "POST"])
def add_driver():

    if request.method == "POST":

        driver = Driver(

            name=request.form["name"],

            license_number=request.form["license_number"],

            phone=request.form["phone"],

            experience=request.form["experience"],

            status=request.form["status"]

        )

        db.session.add(driver)
        db.session.commit()

        flash("Driver Added Successfully!", "success")

        return redirect(url_for("driver.drivers"))

    return render_template("driver_add.html")
"""