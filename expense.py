from flask import Blueprint, request, jsonify, render_template
from sqlalchemy import or_
from datetime import datetime

from database.db import db
from database.models import Expense, Vehicle

expense_bp = Blueprint(
    "expense",
    __name__,
    url_prefix="/expense"
)


# =====================================================
# Expense Management Page
# =====================================================

@expense_bp.route("/")
def expense_page():
    return render_template("expense.html")


# =====================================================
# Get All Expenses
# =====================================================

@expense_bp.route("/api", methods=["GET"])
def get_expenses():

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    search = request.args.get("search", "")
    expense_type = request.args.get("type", "")
    vehicle = request.args.get("vehicle", "")

    query = Expense.query.join(Vehicle)

    # -----------------------------------------
    # Search
    # -----------------------------------------

    if search:
        query = query.filter(
            or_(
                Vehicle.registration_number.ilike(f"%{search}%"),
                Expense.expense_type.ilike(f"%{search}%"),
                Expense.description.ilike(f"%{search}%")
            )
        )

    # -----------------------------------------
    # Expense Type Filter
    # -----------------------------------------

    if expense_type:
        query = query.filter(
            Expense.expense_type == expense_type
        )

    # -----------------------------------------
    # Vehicle Filter
    # -----------------------------------------

    if vehicle:
        query = query.filter(
            Expense.vehicle_id == vehicle
        )

    query = query.order_by(
        Expense.expense_date.desc()
    )

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

        "data": [

            expense.to_dict()

            for expense in pagination.items

        ]

    })


# =====================================================
# Add Expense
# =====================================================

@expense_bp.route("/add", methods=["POST"])
def add_expense():

    data = request.get_json()

    try:

        vehicle_id = data["vehicle_id"]

        expense_type = data["expense_type"]

        amount = float(data["amount"])

        expense_date = datetime.strptime(
            data["expense_date"],
            "%Y-%m-%d"
        ).date()

        description = data.get(
            "description",
            ""
        )

        # ---------------- Validation ----------------

        if amount <= 0:

            return jsonify({

                "success": False,

                "message": "Amount must be greater than zero."

            }), 400

        expense = Expense(

            vehicle_id=vehicle_id,

            expense_type=expense_type,

            amount=amount,

            expense_date=expense_date,

            description=description

        )

        db.session.add(expense)

        db.session.commit()

        return jsonify({

            "success": True,

            "message": "Expense added successfully."

        })

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =====================================================
# Update Expense
# =====================================================

@expense_bp.route("/update/<int:id>", methods=["PUT"])
def update_expense(id):

    expense = Expense.query.get_or_404(id)

    data = request.get_json()

    try:

        expense.vehicle_id = data["vehicle_id"]

        expense.expense_type = data["expense_type"]

        expense.amount = float(data["amount"])

        expense.expense_date = datetime.strptime(
            data["expense_date"],
            "%Y-%m-%d"
        ).date()

        expense.description = data.get(
            "description",
            ""
        )

        db.session.commit()

        return jsonify({

            "success": True,

            "message": "Expense updated successfully."

        })

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =====================================================
# Delete Expense
# =====================================================

@expense_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_expense(id):

    try:

        expense = Expense.query.get_or_404(id)

        db.session.delete(expense)

        db.session.commit()

        return jsonify({

            "success": True,

            "message": "Expense deleted successfully."

        })

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =====================================================
# Vehicle Dropdown
# =====================================================

@expense_bp.route("/vehicles")
def vehicle_dropdown():

    vehicles = Vehicle.query.order_by(
        Vehicle.registration_number
    ).all()

    return jsonify([

        {

            "id": vehicle.id,

            "registration_number": vehicle.registration_number,

            "model": vehicle.model

        }

        for vehicle in vehicles

    ])


# =====================================================
# Dashboard Cards
# =====================================================

@expense_bp.route("/summary")
def expense_summary():

    total_expense = db.session.query(
        db.func.sum(Expense.amount)
    ).scalar() or 0

    total_records = Expense.query.count()

    fuel_cost = db.session.query(
        db.func.sum(Expense.amount)
    ).filter(
        Expense.expense_type == "Fuel"
    ).scalar() or 0

    maintenance_cost = db.session.query(
        db.func.sum(Expense.amount)
    ).filter(
        Expense.expense_type == "Maintenance"
    ).scalar() or 0

    return jsonify({

        "success": True,

        "total_expense": round(total_expense, 2),

        "fuel_cost": round(fuel_cost, 2),

        "maintenance_cost": round(maintenance_cost, 2),

        "records": total_records

    })