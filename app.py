from __future__ import annotations

import csv
import io
import random
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

from flask import (
    Flask,
    Response,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from config import Config
from extensions import csrf, db, migrate
from models import Driver, Expense, FuelLog, Maintenance, Trip, UserProfile, Vehicle


BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)
csrf.init_app(app)
app.url_map.strict_slashes = False


# -----------------------------------------------------------------------------
# Formatting and validation helpers
# -----------------------------------------------------------------------------


def parse_decimal(value: str | None, field_name: str, *, allow_zero: bool = True) -> Decimal:
    try:
        number = Decimal(str(value or "").strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field_name} must be a valid number.") from None

    if number < 0 or (not allow_zero and number == 0):
        operator = "greater than zero" if not allow_zero else "zero or greater"
        raise ValueError(f"{field_name} must be {operator}.")
    return number.quantize(Decimal("0.01"))


def parse_date(value: str | None, field_name: str, *, required: bool = True) -> date | None:
    if not value:
        if required:
            raise ValueError(f"{field_name} is required.")
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"{field_name} must be a valid date.") from None


def required_text(value: str | None, field_name: str, max_length: int = 255) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required.")
    if len(text) > max_length:
        raise ValueError(f"{field_name} must not exceed {max_length} characters.")
    return text


def first_day(value: date) -> date:
    return value.replace(day=1)


def next_month(value: date) -> date:
    return (value.replace(day=28) + timedelta(days=4)).replace(day=1)


def previous_month(value: date) -> date:
    return (value.replace(day=1) - timedelta(days=1)).replace(day=1)


def month_range(value: date) -> tuple[date, date]:
    start = value.replace(day=1)
    return start, next_month(start)


def last_month_starts(end_month: date, count: int = 6) -> list[date]:
    months: list[date] = []
    cursor = first_day(end_month)
    for _ in range(count):
        months.append(cursor)
        cursor = previous_month(cursor)
    return list(reversed(months))


def sum_decimal(values: Iterable[Decimal | None]) -> Decimal:
    total = Decimal("0")
    for value in values:
        total += Decimal(value or 0)
    return total


def money_short(value: Decimal | float | int | None) -> str:
    number = Decimal(value or 0)
    if abs(number) >= Decimal("10000000"):
        return f"₹{number / Decimal('10000000'):.2f}Cr"
    if abs(number) >= Decimal("100000"):
        return f"₹{number / Decimal('100000'):.2f}L"
    return f"₹{format_indian_number(number)}"


def format_indian_number(value: Decimal | float | int | None, decimals: int = 0) -> str:
    number = Decimal(value or 0)
    sign = "-" if number < 0 else ""
    number = abs(number)
    fixed = f"{number:.{decimals}f}"
    integer, dot, fraction = fixed.partition(".")
    if len(integer) > 3:
        last_three = integer[-3:]
        remaining = integer[:-3]
        groups = []
        while remaining:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        integer = ",".join(groups + [last_three])
    return f"{sign}{integer}{dot}{fraction}" if decimals else f"{sign}{integer}"


@app.template_filter("inr")
def inr_filter(value):
    return f"₹{format_indian_number(value)}"


@app.template_filter("datefmt")
def date_filter(value):
    return value.strftime("%d %b %Y") if value else "—"


@app.template_filter("decimal")
def decimal_filter(value, places=2):
    return f"{Decimal(value or 0):.{int(places)}f}"


def save_or_flash(operation, success_message: str, fallback_endpoint: str, **fallback_values):
    try:
        operation()
        db.session.commit()
        flash(success_message, "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")
    except IntegrityError:
        db.session.rollback()
        flash("A record with the same unique value already exists.", "danger")
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Database operation failed")
        flash("The database operation failed. Please verify the entered data.", "danger")
    return redirect(url_for(fallback_endpoint, **fallback_values))


def sync_generated_expense(
    *,
    source_type: str,
    source_id: int,
    vehicle_id: int,
    expense_date: date,
    amount: Decimal,
    description: str,
    status: str = "Completed",
) -> None:
    expense = db.session.scalar(
        select(Expense).where(
            Expense.source_type == source_type,
            Expense.source_id == source_id,
        )
    )
    if expense is None:
        expense = Expense(source_type=source_type, source_id=source_id)
        db.session.add(expense)

    expense.vehicle_id = vehicle_id
    expense.expense_date = expense_date
    expense.category = "Fuel" if source_type == "fuel" else "Maintenance"
    expense.description = description
    expense.amount = amount
    expense.payment_method = "System linked"
    expense.status = status


def delete_generated_expense(source_type: str, source_id: int) -> None:
    expense = db.session.scalar(
        select(Expense).where(
            Expense.source_type == source_type,
            Expense.source_id == source_id,
        )
    )
    if expense:
        db.session.delete(expense)


# -----------------------------------------------------------------------------
# Shared context
# -----------------------------------------------------------------------------


@app.context_processor
def inject_global_context():
    profile = None
    notifications = []
    try:
        profile = db.session.scalar(select(UserProfile).limit(1))
        today = date.today()
        due_maintenance = db.session.scalar(
            select(func.count(Maintenance.id)).where(
                Maintenance.next_service_date.is_not(None),
                Maintenance.next_service_date <= today + timedelta(days=14),
            )
        ) or 0
        expiring_licenses = db.session.scalar(
            select(func.count(Driver.id)).where(
                Driver.license_expiry <= today + timedelta(days=30)
            )
        ) or 0
        inactive_vehicles = db.session.scalar(
            select(func.count(Vehicle.id)).where(Vehicle.status != "Active")
        ) or 0
        notifications = [
            {
                "title": f"{due_maintenance} service task(s) due",
                "url": url_for("maintenance"),
                "icon": "bi-tools",
            },
            {
                "title": f"{expiring_licenses} licence(s) expiring",
                "url": url_for("drivers"),
                "icon": "bi-person-vcard",
            },
            {
                "title": f"{inactive_vehicles} vehicle(s) need attention",
                "url": url_for("vehicles"),
                "icon": "bi-truck-front",
            },
        ]
    except SQLAlchemyError:
        db.session.rollback()

    return {
        "global_profile": profile,
        "global_notifications": notifications,
        "dark_theme_enabled": session.get("dark_theme", True),
    }


# -----------------------------------------------------------------------------
# Dashboard
# -----------------------------------------------------------------------------


@app.get("/")
def dashboard():
    today = date.today()
    current_start, current_end = month_range(today)
    previous_start = previous_month(current_start)

    total_vehicles = db.session.scalar(select(func.count(Vehicle.id))) or 0
    active_vehicles = db.session.scalar(
        select(func.count(Vehicle.id)).where(Vehicle.status == "Active")
    ) or 0
    drivers = db.session.scalar(select(func.count(Driver.id))) or 0
    available_drivers = db.session.scalar(
        select(func.count(Driver.id)).where(Driver.status == "Available")
    ) or 0

    current_fuel_cost = db.session.scalar(
        select(func.coalesce(func.sum(FuelLog.total_cost), 0)).where(
            FuelLog.fuel_date >= current_start,
            FuelLog.fuel_date < current_end,
        )
    ) or Decimal("0")
    previous_fuel_cost = db.session.scalar(
        select(func.coalesce(func.sum(FuelLog.total_cost), 0)).where(
            FuelLog.fuel_date >= previous_start,
            FuelLog.fuel_date < current_start,
        )
    ) or Decimal("0")

    if previous_fuel_cost:
        change_pct = ((current_fuel_cost - previous_fuel_cost) / previous_fuel_cost) * 100
        change_text = f"{abs(change_pct):.1f}% {'higher' if change_pct > 0 else 'lower'} than last month"
    else:
        change_text = "No previous-month comparison"

    utilization = (Decimal(active_vehicles) / Decimal(total_vehicles) * 100) if total_vehicles else Decimal("0")

    recent_trips = db.session.scalars(
        select(Trip)
        .order_by(Trip.start_date.desc(), Trip.id.desc())
        .limit(5)
    ).all()

    months = last_month_starts(today, 6)
    performance_labels = [month.strftime("%b") for month in months]
    performance_distance = []
    performance_trips = []
    for month in months:
        start, end = month_range(month)
        performance_distance.append(
            float(
                db.session.scalar(
                    select(func.coalesce(func.sum(Trip.distance_km), 0)).where(
                        Trip.start_date >= start,
                        Trip.start_date < end,
                        Trip.status == "Completed",
                    )
                )
                or 0
            )
        )
        performance_trips.append(
            int(
                db.session.scalar(
                    select(func.count(Trip.id)).where(
                        Trip.start_date >= start,
                        Trip.start_date < end,
                        Trip.status == "Completed",
                    )
                )
                or 0
            )
        )

    statuses = ["Active", "Maintenance", "Inactive"]
    status_values = [
        int(
            db.session.scalar(
                select(func.count(Vehicle.id)).where(Vehicle.status == status)
            )
            or 0
        )
        for status in statuses
    ]

    stats = {
        "total_vehicles": total_vehicles,
        "active_vehicles": active_vehicles,
        "drivers": drivers,
        "available_drivers": available_drivers,
        "fuel_cost": money_short(current_fuel_cost),
        "fuel_change": change_text,
        "fleet_utilization": f"{utilization:.1f}%",
        "utilization_change": "Based on currently active vehicles",
    }

    chart_data = {
        "performance": {
            "labels": performance_labels,
            "distance": performance_distance,
            "trips": performance_trips,
        },
        "status": {"labels": statuses, "values": status_values},
    }

    return render_template(
        "dashboard.html",
        page_title="Dashboard",
        page_subtitle="Smart fleet management at a glance",
        stats=stats,
        recent_trips=recent_trips,
        chart_data=chart_data,
    )


# -----------------------------------------------------------------------------
# Fuel management
# -----------------------------------------------------------------------------


@app.get("/fuel")
def fuel():
    query_text = request.args.get("q", "").strip()
    vehicle_id = request.args.get("vehicle_id", type=int)

    statement = select(FuelLog).order_by(FuelLog.fuel_date.desc(), FuelLog.id.desc())
    if query_text:
        statement = statement.join(Vehicle).outerjoin(Driver).where(
            or_(
                Vehicle.registration_number.ilike(f"%{query_text}%"),
                Driver.name.ilike(f"%{query_text}%"),
                FuelLog.station.ilike(f"%{query_text}%"),
                FuelLog.invoice_number.ilike(f"%{query_text}%"),
            )
        )
    if vehicle_id:
        statement = statement.where(FuelLog.vehicle_id == vehicle_id)

    fuel_records = db.session.scalars(statement.limit(100)).unique().all()
    vehicles_list = db.session.scalars(select(Vehicle).order_by(Vehicle.registration_number)).all()
    drivers_list = db.session.scalars(select(Driver).order_by(Driver.name)).all()
    trips_list = db.session.scalars(select(Trip).order_by(Trip.start_date.desc()).limit(100)).all()

    today = date.today()
    month_start, month_end = month_range(today)
    monthly_logs = db.session.scalars(
        select(FuelLog).where(FuelLog.fuel_date >= month_start, FuelLog.fuel_date < month_end)
    ).all()
    total_liters = sum_decimal(log.liters for log in monthly_logs)
    total_cost = sum_decimal(log.total_cost for log in monthly_logs)
    average_mileage = (
        sum_decimal(log.mileage_kmpl for log in monthly_logs) / len(monthly_logs)
        if monthly_logs
        else Decimal("0")
    )

    consuming_row = db.session.execute(
        select(Vehicle.registration_number, func.sum(FuelLog.liters).label("liters"))
        .join(FuelLog, FuelLog.vehicle_id == Vehicle.id)
        .where(FuelLog.fuel_date >= month_start, FuelLog.fuel_date < month_end)
        .group_by(Vehicle.id, Vehicle.registration_number)
        .order_by(func.sum(FuelLog.liters).desc())
        .limit(1)
    ).first()

    stats = {
        "total_used": f"{format_indian_number(total_liters)} L",
        "fuel_cost": f"₹{format_indian_number(total_cost)}",
        "average_mileage": f"{average_mileage:.1f} km/L",
        "most_consuming_vehicle": consuming_row.registration_number if consuming_row else "—",
    }

    months = last_month_starts(today, 6)
    labels = [month.strftime("%b") for month in months]
    costs = []
    budgets = []
    for month in months:
        start, end = month_range(month)
        value = db.session.scalar(
            select(func.coalesce(func.sum(FuelLog.total_cost), 0)).where(
                FuelLog.fuel_date >= start,
                FuelLog.fuel_date < end,
            )
        ) or 0
        costs.append(round(float(value) / 100000, 2))
        budgets.append(round(max(float(value) / 100000 * 1.08, 1), 2))

    type_rows = db.session.execute(
        select(Vehicle.vehicle_type, func.coalesce(func.sum(FuelLog.liters), 0))
        .join(FuelLog, FuelLog.vehicle_id == Vehicle.id)
        .group_by(Vehicle.vehicle_type)
        .order_by(func.sum(FuelLog.liters).desc())
    ).all()

    chart_data = {
        "cost": {"labels": labels, "actual": costs, "budget": budgets},
        "distribution": {
            "labels": [row[0] for row in type_rows],
            "values": [float(row[1]) for row in type_rows],
        },
    }

    return render_template(
        "fuel.html",
        page_title="Fuel Management",
        page_subtitle="Monitor consumption, mileage and fuel spending",
        stats=stats,
        fuel_records=fuel_records,
        vehicles=vehicles_list,
        drivers=drivers_list,
        trips=trips_list,
        chart_data=chart_data,
        filters={"q": query_text, "vehicle_id": vehicle_id},
        edit_id=request.args.get("edit", type=int),
    )


@app.post("/fuel/save")
def fuel_save():
    record_id = request.form.get("id", type=int)

    def operation():
        vehicle_id = request.form.get("vehicle_id", type=int)
        driver_id = request.form.get("driver_id", type=int)
        trip_id = request.form.get("trip_id", type=int)
        vehicle = db.session.get(Vehicle, vehicle_id)
        if not vehicle:
            raise ValueError("Please select a valid vehicle.")
        if driver_id and not db.session.get(Driver, driver_id):
            raise ValueError("Please select a valid driver.")
        if trip_id and not db.session.get(Trip, trip_id):
            raise ValueError("Please select a valid trip.")

        record = db.session.get(FuelLog, record_id) if record_id else FuelLog()
        if record_id and not record:
            abort(404)
        if not record_id:
            db.session.add(record)

        record.vehicle_id = vehicle_id
        record.driver_id = driver_id
        record.trip_id = trip_id
        record.fuel_date = parse_date(request.form.get("fuel_date"), "Fuel date")
        record.liters = parse_decimal(request.form.get("liters"), "Fuel quantity", allow_zero=False)
        record.total_cost = parse_decimal(request.form.get("total_cost"), "Total cost", allow_zero=False)
        record.odometer_km = parse_decimal(request.form.get("odometer_km"), "Odometer")
        record.mileage_kmpl = parse_decimal(request.form.get("mileage_kmpl"), "Mileage")
        record.station = required_text(request.form.get("station"), "Fuel station", 180)
        record.invoice_number = (request.form.get("invoice_number") or "").strip() or None

        vehicle.odometer_km = max(Decimal(vehicle.odometer_km or 0), record.odometer_km)
        db.session.flush()
        sync_generated_expense(
            source_type="fuel",
            source_id=record.id,
            vehicle_id=record.vehicle_id,
            expense_date=record.fuel_date,
            amount=record.total_cost,
            description=f"Fuel refill at {record.station}",
        )

    return save_or_flash(
        operation,
        "Fuel record saved successfully.",
        "fuel",
    )


@app.post("/fuel/<int:record_id>/delete")
def fuel_delete(record_id: int):
    record = db.session.get(FuelLog, record_id)
    if not record:
        abort(404)

    def operation():
        delete_generated_expense("fuel", record.id)
        db.session.delete(record)

    return save_or_flash(operation, "Fuel record deleted.", "fuel")


# -----------------------------------------------------------------------------
# Expense management
# -----------------------------------------------------------------------------


# Compatibility alias: both /expense and /expenses open the same module.
@app.get("/expenses")
def expenses_alias():
    return redirect(url_for("expense"))


@app.get("/expense")
def expense():
    query_text = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    statement = select(Expense).order_by(Expense.expense_date.desc(), Expense.id.desc())
    if query_text:
        statement = statement.outerjoin(Vehicle).where(
            or_(
                Vehicle.registration_number.ilike(f"%{query_text}%"),
                Expense.category.ilike(f"%{query_text}%"),
                Expense.description.ilike(f"%{query_text}%"),
                Expense.payment_method.ilike(f"%{query_text}%"),
            )
        )
    if category:
        statement = statement.where(Expense.category == category)

    records = db.session.scalars(statement.limit(120)).unique().all()
    vehicles_list = db.session.scalars(select(Vehicle).order_by(Vehicle.registration_number)).all()

    today = date.today()
    start, end = month_range(today)
    month_expenses = db.session.scalars(
        select(Expense).where(Expense.expense_date >= start, Expense.expense_date < end)
    ).all()

    category_totals: dict[str, Decimal] = {}
    for item in month_expenses:
        category_totals[item.category] = category_totals.get(item.category, Decimal("0")) + Decimal(item.amount or 0)

    fuel_total = category_totals.get("Fuel", Decimal("0"))
    maintenance_total = category_totals.get("Maintenance", Decimal("0"))
    other_total = sum_decimal(
        value for key, value in category_totals.items() if key not in {"Fuel", "Maintenance"}
    )
    total = sum_decimal(item.amount for item in month_expenses)

    stats = {
        "total": f"₹{format_indian_number(total)}",
        "fuel": f"₹{format_indian_number(fuel_total)}",
        "maintenance": f"₹{format_indian_number(maintenance_total)}",
        "other": f"₹{format_indian_number(other_total)}",
    }

    categories = ["Fuel", "Maintenance", "Insurance", "Toll", "Other"]
    breakdown_values = [float(category_totals.get(item, Decimal("0"))) for item in categories]

    months = last_month_starts(today, 6)
    labels = [month.strftime("%b") for month in months]
    trend = {"Fuel": [], "Maintenance": [], "Other": []}
    for month in months:
        month_start, month_end = month_range(month)
        month_rows = db.session.execute(
            select(Expense.category, func.coalesce(func.sum(Expense.amount), 0))
            .where(Expense.expense_date >= month_start, Expense.expense_date < month_end)
            .group_by(Expense.category)
        ).all()
        values = {row[0]: Decimal(row[1] or 0) for row in month_rows}
        trend["Fuel"].append(round(float(values.get("Fuel", 0)) / 100000, 2))
        trend["Maintenance"].append(round(float(values.get("Maintenance", 0)) / 100000, 2))
        trend["Other"].append(
            round(
                float(sum_decimal(v for k, v in values.items() if k not in {"Fuel", "Maintenance"}))
                / 100000,
                2,
            )
        )

    chart_data = {
        "breakdown": {"labels": categories, "values": breakdown_values},
        "trend": {"labels": labels, **trend},
    }

    return render_template(
        "expenses.html",
        page_title="Expense Management",
        page_subtitle="Track, review and control fleet operating expenses",
        stats=stats,
        expense_records=records,
        vehicles=vehicles_list,
        categories=categories,
        chart_data=chart_data,
        filters={"q": query_text, "category": category},
        edit_id=request.args.get("edit", type=int),
    )


@app.post("/expense/save")
def expense_save():
    record_id = request.form.get("id", type=int)

    def operation():
        vehicle_id = request.form.get("vehicle_id", type=int)
        if vehicle_id and not db.session.get(Vehicle, vehicle_id):
            raise ValueError("Please select a valid vehicle.")

        record = db.session.get(Expense, record_id) if record_id else Expense(source_type="manual")
        if record_id and not record:
            abort(404)
        if not record_id:
            db.session.add(record)

        expense_date = parse_date(request.form.get("expense_date"), "Expense date")
        amount = parse_decimal(request.form.get("amount"), "Amount", allow_zero=False)
        description = required_text(request.form.get("description"), "Description", 255)
        payment_method = required_text(request.form.get("payment_method"), "Payment method", 60)
        status = required_text(request.form.get("status"), "Status", 30)
        requested_category = required_text(request.form.get("category"), "Category", 80)

        # Manual expenses can be edited normally.
        if not record.is_generated:
            record.vehicle_id = vehicle_id
            record.expense_date = expense_date
            record.category = requested_category
            record.description = description
            record.amount = amount
            record.payment_method = payment_method
            record.status = status
            record.source_type = "manual"
            record.source_id = None
            return

        # Linked fuel expenses update their source fuel record as well.
        if record.source_type == "fuel":
            source = db.session.get(FuelLog, record.source_id)
            if not source:
                raise ValueError("The linked fuel record no longer exists.")
            if not vehicle_id:
                raise ValueError("A linked fuel expense must have a vehicle.")

            source.vehicle_id = vehicle_id
            source.fuel_date = expense_date
            source.total_cost = amount

            record.vehicle_id = vehicle_id
            record.expense_date = expense_date
            record.category = "Fuel"
            record.description = description
            record.amount = amount
            record.payment_method = payment_method
            record.status = status
            return

        # Linked maintenance expenses update their source maintenance record as well.
        if record.source_type == "maintenance":
            source = db.session.get(Maintenance, record.source_id)
            if not source:
                raise ValueError("The linked maintenance record no longer exists.")
            if not vehicle_id:
                raise ValueError("A linked maintenance expense must have a vehicle.")

            source.vehicle_id = vehicle_id
            source.service_date = expense_date
            source.cost = amount
            source.description = description

            record.vehicle_id = vehicle_id
            record.expense_date = expense_date
            record.category = "Maintenance"
            record.description = description
            record.amount = amount
            record.payment_method = payment_method
            record.status = status
            return

        raise ValueError("Unsupported linked expense type.")

    return save_or_flash(operation, "Expense saved successfully.", "expense")


@app.post("/expense/<int:record_id>/delete")
def expense_delete(record_id: int):
    record = db.session.get(Expense, record_id)
    if not record:
        abort(404)

    def operation():
        if record.source_type == "fuel" and record.source_id:
            source = db.session.get(FuelLog, record.source_id)
            if source:
                db.session.delete(source)
        elif record.source_type == "maintenance" and record.source_id:
            source = db.session.get(Maintenance, record.source_id)
            if source:
                db.session.delete(source)
        db.session.delete(record)

    return save_or_flash(operation, "Expense and linked source record deleted.", "expense")


# -----------------------------------------------------------------------------
# Vehicle management
# -----------------------------------------------------------------------------


@app.get("/vehicles")
def vehicles():
    query_text = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    statement = select(Vehicle).order_by(Vehicle.registration_number)
    if query_text:
        statement = statement.where(
            or_(
                Vehicle.registration_number.ilike(f"%{query_text}%"),
                Vehicle.model.ilike(f"%{query_text}%"),
                Vehicle.vehicle_type.ilike(f"%{query_text}%"),
            )
        )
    if status:
        statement = statement.where(Vehicle.status == status)
    records = db.session.scalars(statement).all()

    stats = {
        "total": db.session.scalar(select(func.count(Vehicle.id))) or 0,
        "active": db.session.scalar(select(func.count(Vehicle.id)).where(Vehicle.status == "Active")) or 0,
        "maintenance": db.session.scalar(select(func.count(Vehicle.id)).where(Vehicle.status == "Maintenance")) or 0,
        "inactive": db.session.scalar(select(func.count(Vehicle.id)).where(Vehicle.status == "Inactive")) or 0,
    }
    return render_template(
        "vehicles.html",
        page_title="Vehicles",
        page_subtitle="Vehicle registry and fleet availability",
        records=records,
        stats=stats,
        filters={"q": query_text, "status": status},
        edit_id=request.args.get("edit", type=int),
        open_add=request.args.get("open") == "add",
    )


@app.post("/vehicles/save")
def vehicle_save():
    record_id = request.form.get("id", type=int)

    def operation():
        record = db.session.get(Vehicle, record_id) if record_id else Vehicle()
        if record_id and not record:
            abort(404)
        if not record_id:
            db.session.add(record)
        record.registration_number = required_text(request.form.get("registration_number"), "Registration number", 30).upper()
        record.model = required_text(request.form.get("model"), "Model", 120)
        record.vehicle_type = required_text(request.form.get("vehicle_type"), "Vehicle type", 80)
        record.capacity_kg = parse_decimal(request.form.get("capacity_kg"), "Capacity")
        record.acquisition_cost = parse_decimal(request.form.get("acquisition_cost"), "Acquisition cost")
        record.odometer_km = parse_decimal(request.form.get("odometer_km"), "Odometer")
        record.status = required_text(request.form.get("status"), "Status", 30)

    return save_or_flash(operation, "Vehicle saved successfully.", "vehicles")


@app.post("/vehicles/<int:record_id>/delete")
def vehicle_delete(record_id: int):
    record = db.session.get(Vehicle, record_id)
    if not record:
        abort(404)

    def operation():
        db.session.delete(record)

    return save_or_flash(operation, "Vehicle deleted.", "vehicles")


# -----------------------------------------------------------------------------
# Driver management
# -----------------------------------------------------------------------------


@app.get("/drivers")
def drivers():
    query_text = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    statement = select(Driver).order_by(Driver.name)
    if query_text:
        statement = statement.where(
            or_(
                Driver.name.ilike(f"%{query_text}%"),
                Driver.phone.ilike(f"%{query_text}%"),
                Driver.license_number.ilike(f"%{query_text}%"),
                Driver.email.ilike(f"%{query_text}%"),
            )
        )
    if status:
        statement = statement.where(Driver.status == status)
    records = db.session.scalars(statement).all()
    today = date.today()
    stats = {
        "total": db.session.scalar(select(func.count(Driver.id))) or 0,
        "available": db.session.scalar(select(func.count(Driver.id)).where(Driver.status == "Available")) or 0,
        "assigned": db.session.scalar(select(func.count(Driver.id)).where(Driver.status == "Assigned")) or 0,
        "expiring": db.session.scalar(select(func.count(Driver.id)).where(Driver.license_expiry <= today + timedelta(days=30))) or 0,
    }
    return render_template(
        "drivers.html",
        page_title="Drivers",
        page_subtitle="Driver profiles, licences and availability",
        records=records,
        stats=stats,
        filters={"q": query_text, "status": status},
        edit_id=request.args.get("edit", type=int),
    )


@app.post("/drivers/save")
def driver_save():
    record_id = request.form.get("id", type=int)

    def operation():
        record = db.session.get(Driver, record_id) if record_id else Driver()
        if record_id and not record:
            abort(404)
        if not record_id:
            db.session.add(record)
        record.name = required_text(request.form.get("name"), "Driver name", 120)
        record.phone = required_text(request.form.get("phone"), "Phone", 30)
        record.email = (request.form.get("email") or "").strip() or None
        record.license_number = required_text(request.form.get("license_number"), "Licence number", 80).upper()
        record.license_expiry = parse_date(request.form.get("license_expiry"), "Licence expiry")
        record.status = required_text(request.form.get("status"), "Status", 30)

    return save_or_flash(operation, "Driver saved successfully.", "drivers")


@app.post("/drivers/<int:record_id>/delete")
def driver_delete(record_id: int):
    record = db.session.get(Driver, record_id)
    if not record:
        abort(404)

    def operation():
        db.session.delete(record)

    return save_or_flash(operation, "Driver deleted.", "drivers")


# -----------------------------------------------------------------------------
# Trip management
# -----------------------------------------------------------------------------


@app.get("/trips")
def trips():
    query_text = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    statement = select(Trip).order_by(Trip.start_date.desc(), Trip.id.desc())
    if query_text:
        statement = statement.join(Vehicle).join(Driver).where(
            or_(
                Vehicle.registration_number.ilike(f"%{query_text}%"),
                Driver.name.ilike(f"%{query_text}%"),
                Trip.origin.ilike(f"%{query_text}%"),
                Trip.destination.ilike(f"%{query_text}%"),
            )
        )
    if status:
        statement = statement.where(Trip.status == status)
    records = db.session.scalars(statement).unique().all()
    vehicles_list = db.session.scalars(select(Vehicle).order_by(Vehicle.registration_number)).all()
    drivers_list = db.session.scalars(select(Driver).order_by(Driver.name)).all()
    stats = {
        "total": db.session.scalar(select(func.count(Trip.id))) or 0,
        "completed": db.session.scalar(select(func.count(Trip.id)).where(Trip.status == "Completed")) or 0,
        "transit": db.session.scalar(select(func.count(Trip.id)).where(Trip.status == "In Transit")) or 0,
        "scheduled": db.session.scalar(select(func.count(Trip.id)).where(Trip.status == "Scheduled")) or 0,
    }
    return render_template(
        "trips.html",
        page_title="Trips",
        page_subtitle="Plan, dispatch and track fleet journeys",
        records=records,
        vehicles=vehicles_list,
        drivers=drivers_list,
        stats=stats,
        filters={"q": query_text, "status": status},
        edit_id=request.args.get("edit", type=int),
        view_id=request.args.get("view", type=int),
    )


@app.post("/trips/save")
def trip_save():
    record_id = request.form.get("id", type=int)

    def operation():
        vehicle_id = request.form.get("vehicle_id", type=int)
        driver_id = request.form.get("driver_id", type=int)
        if not db.session.get(Vehicle, vehicle_id):
            raise ValueError("Please select a valid vehicle.")
        if not db.session.get(Driver, driver_id):
            raise ValueError("Please select a valid driver.")

        record = db.session.get(Trip, record_id) if record_id else Trip()
        if record_id and not record:
            abort(404)
        if not record_id:
            db.session.add(record)
        record.vehicle_id = vehicle_id
        record.driver_id = driver_id
        record.origin = required_text(request.form.get("origin"), "Origin", 140)
        record.destination = required_text(request.form.get("destination"), "Destination", 140)
        record.start_date = parse_date(request.form.get("start_date"), "Start date")
        record.end_date = parse_date(request.form.get("end_date"), "End date", required=False)
        record.distance_km = parse_decimal(request.form.get("distance_km"), "Distance")
        record.revenue = parse_decimal(request.form.get("revenue"), "Revenue")
        record.status = required_text(request.form.get("status"), "Status", 30)

        vehicle = db.session.get(Vehicle, vehicle_id)
        driver = db.session.get(Driver, driver_id)
        if record.status == "In Transit":
            vehicle.status = "Active"
            driver.status = "Assigned"
        elif record.status == "Completed":
            driver.status = "Available"
            vehicle.odometer_km = Decimal(vehicle.odometer_km or 0) + record.distance_km

    return save_or_flash(operation, "Trip saved successfully.", "trips")


@app.post("/trips/<int:record_id>/delete")
def trip_delete(record_id: int):
    record = db.session.get(Trip, record_id)
    if not record:
        abort(404)

    def operation():
        db.session.delete(record)

    return save_or_flash(operation, "Trip deleted.", "trips")


# -----------------------------------------------------------------------------
# Maintenance management
# -----------------------------------------------------------------------------


@app.get("/maintenance")
def maintenance():
    query_text = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    statement = select(Maintenance).order_by(Maintenance.service_date.desc(), Maintenance.id.desc())
    if query_text:
        statement = statement.join(Vehicle).where(
            or_(
                Vehicle.registration_number.ilike(f"%{query_text}%"),
                Maintenance.category.ilike(f"%{query_text}%"),
                Maintenance.description.ilike(f"%{query_text}%"),
            )
        )
    if status:
        statement = statement.where(Maintenance.status == status)
    records = db.session.scalars(statement).unique().all()
    vehicles_list = db.session.scalars(select(Vehicle).order_by(Vehicle.registration_number)).all()
    today = date.today()
    stats = {
        "total": db.session.scalar(select(func.count(Maintenance.id))) or 0,
        "completed": db.session.scalar(select(func.count(Maintenance.id)).where(Maintenance.status == "Completed")) or 0,
        "scheduled": db.session.scalar(select(func.count(Maintenance.id)).where(Maintenance.status == "Scheduled")) or 0,
        "due": db.session.scalar(
            select(func.count(Maintenance.id)).where(
                Maintenance.next_service_date.is_not(None),
                Maintenance.next_service_date <= today + timedelta(days=14),
            )
        ) or 0,
    }
    return render_template(
        "maintenance.html",
        page_title="Maintenance",
        page_subtitle="Preventive service and repair management",
        records=records,
        vehicles=vehicles_list,
        stats=stats,
        filters={"q": query_text, "status": status},
        edit_id=request.args.get("edit", type=int),
    )


@app.post("/maintenance/save")
def maintenance_save():
    record_id = request.form.get("id", type=int)

    def operation():
        vehicle_id = request.form.get("vehicle_id", type=int)
        vehicle = db.session.get(Vehicle, vehicle_id)
        if not vehicle:
            raise ValueError("Please select a valid vehicle.")

        record = db.session.get(Maintenance, record_id) if record_id else Maintenance()
        if record_id and not record:
            abort(404)
        if not record_id:
            db.session.add(record)
        record.vehicle_id = vehicle_id
        record.service_date = parse_date(request.form.get("service_date"), "Service date")
        record.category = required_text(request.form.get("category"), "Category", 80)
        record.description = required_text(request.form.get("description"), "Description", 255)
        record.cost = parse_decimal(request.form.get("cost"), "Cost")
        record.next_service_date = parse_date(request.form.get("next_service_date"), "Next service date", required=False)
        record.status = required_text(request.form.get("status"), "Status", 30)

        if record.status in {"Scheduled", "In Progress"}:
            vehicle.status = "Maintenance"
        elif record.status == "Completed" and vehicle.status == "Maintenance":
            vehicle.status = "Active"

        db.session.flush()
        sync_generated_expense(
            source_type="maintenance",
            source_id=record.id,
            vehicle_id=record.vehicle_id,
            expense_date=record.service_date,
            amount=record.cost,
            description=record.description,
            status="Completed" if record.status == "Completed" else "Pending",
        )

    return save_or_flash(operation, "Maintenance record saved successfully.", "maintenance")


@app.post("/maintenance/<int:record_id>/delete")
def maintenance_delete(record_id: int):
    record = db.session.get(Maintenance, record_id)
    if not record:
        abort(404)

    def operation():
        delete_generated_expense("maintenance", record.id)
        db.session.delete(record)

    return save_or_flash(operation, "Maintenance record deleted.", "maintenance")


# -----------------------------------------------------------------------------
# Reports and analytics
# -----------------------------------------------------------------------------


def report_data(selected_month: date) -> dict:
    month_start, month_end = month_range(selected_month)
    months = last_month_starts(selected_month, 6)

    total_distance = db.session.scalar(
        select(func.coalesce(func.sum(Trip.distance_km), 0)).where(
            Trip.start_date >= month_start,
            Trip.start_date < month_end,
            Trip.status == "Completed",
        )
    ) or Decimal("0")
    total_liters = db.session.scalar(
        select(func.coalesce(func.sum(FuelLog.liters), 0)).where(
            FuelLog.fuel_date >= month_start,
            FuelLog.fuel_date < month_end,
        )
    ) or Decimal("0")
    fuel_efficiency = (Decimal(total_distance) / Decimal(total_liters)) if total_liters else Decimal("0")

    operating_cost = db.session.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.expense_date >= month_start,
            Expense.expense_date < month_end,
        )
    ) or Decimal("0")
    revenue = db.session.scalar(
        select(func.coalesce(func.sum(Trip.revenue), 0)).where(
            Trip.start_date >= month_start,
            Trip.start_date < month_end,
        )
    ) or Decimal("0")
    acquisition = db.session.scalar(select(func.coalesce(func.sum(Vehicle.acquisition_cost), 0))) or Decimal("0")
    roi = ((Decimal(revenue) - Decimal(operating_cost)) / Decimal(acquisition) * 100) if acquisition else Decimal("0")

    total_vehicles = db.session.scalar(select(func.count(Vehicle.id))) or 0
    active_vehicles = db.session.scalar(select(func.count(Vehicle.id)).where(Vehicle.status == "Active")) or 0
    utilization = (Decimal(active_vehicles) / Decimal(total_vehicles) * 100) if total_vehicles else Decimal("0")

    labels = [month.strftime("%b") for month in months]
    fuel_costs = []
    budgets = []
    trip_counts = []
    on_time = []
    for month in months:
        start, end = month_range(month)
        fuel_value = db.session.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.expense_date >= start,
                Expense.expense_date < end,
                Expense.category == "Fuel",
            )
        ) or Decimal("0")
        fuel_costs.append(round(float(fuel_value) / 100000, 2))
        budgets.append(round(max(float(fuel_value) / 100000 * 1.08, 1), 2))
        total = db.session.scalar(
            select(func.count(Trip.id)).where(Trip.start_date >= start, Trip.start_date < end)
        ) or 0
        completed = db.session.scalar(
            select(func.count(Trip.id)).where(
                Trip.start_date >= start,
                Trip.start_date < end,
                Trip.status == "Completed",
            )
        ) or 0
        trip_counts.append(int(completed))
        on_time.append(round((completed / total * 100) if total else 0, 1))

    vehicle_rows = db.session.execute(
        select(
            Vehicle.registration_number,
            func.coalesce(func.sum(Expense.amount), 0),
        )
        .outerjoin(Expense, Expense.vehicle_id == Vehicle.id)
        .group_by(Vehicle.id, Vehicle.registration_number)
        .order_by(func.sum(Expense.amount).desc())
        .limit(5)
    ).all()

    vehicle_labels = [row[0][-6:] for row in vehicle_rows]
    vehicle_fuel = []
    vehicle_maintenance = []
    for registration, _ in vehicle_rows:
        vehicle = db.session.scalar(select(Vehicle).where(Vehicle.registration_number == registration))
        fuel_value = db.session.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.vehicle_id == vehicle.id,
                Expense.category == "Fuel",
            )
        ) or Decimal("0")
        maintenance_value = db.session.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.vehicle_id == vehicle.id,
                Expense.category == "Maintenance",
            )
        ) or Decimal("0")
        vehicle_fuel.append(round(float(fuel_value) / 100000, 2))
        vehicle_maintenance.append(round(float(maintenance_value) / 100000, 2))

    status_labels = ["Active", "Maintenance", "Inactive"]
    status_values = [
        int(db.session.scalar(select(func.count(Vehicle.id)).where(Vehicle.status == status)) or 0)
        for status in status_labels
    ]

    category_rows = db.session.execute(
        select(Expense.category, func.coalesce(func.sum(Expense.amount), 0))
        .where(Expense.expense_date >= month_start, Expense.expense_date < month_end)
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
    ).all()

    highest_fuel_vehicle = db.session.execute(
        select(Vehicle.registration_number, func.sum(FuelLog.liters))
        .join(FuelLog, FuelLog.vehicle_id == Vehicle.id)
        .where(FuelLog.fuel_date >= month_start, FuelLog.fuel_date < month_end)
        .group_by(Vehicle.id, Vehicle.registration_number)
        .order_by(func.sum(FuelLog.liters).desc())
        .limit(1)
    ).first()

    insights = [
        {
            "class": "success",
            "icon": "bi-check2-circle",
            "title": f"Fleet utilization is {utilization:.1f}%",
            "text": "Use available vehicles for upcoming short-distance assignments before outsourcing capacity.",
        },
        {
            "class": "warning",
            "icon": "bi-exclamation-triangle",
            "title": f"{highest_fuel_vehicle[0] if highest_fuel_vehicle else 'No vehicle'} has the highest fuel use",
            "text": "Review tyre pressure, route pattern, load profile and engine performance.",
        },
        {
            "class": "info",
            "icon": "bi-lightbulb",
            "title": f"Operational cost is {money_short(operating_cost)}",
            "text": "Compare vehicle-level fuel and maintenance spending before the next dispatch plan.",
        },
    ]

    return {
        "stats": {
            "fuel_efficiency": f"{fuel_efficiency:.2f} km/L",
            "operational_cost": money_short(operating_cost),
            "vehicle_roi": f"{roi:.2f}%",
            "fleet_utilization": f"{utilization:.1f}%",
        },
        "charts": {
            "fuel": {"labels": labels, "actual": fuel_costs, "budget": budgets},
            "vehicle_cost": {
                "labels": vehicle_labels,
                "fuel": vehicle_fuel,
                "maintenance": vehicle_maintenance,
            },
            "trips": {"labels": labels, "completed": trip_counts, "on_time": on_time},
            "utilization": {"labels": status_labels, "values": status_values},
            "expense": {
                "labels": [row[0] for row in category_rows],
                "values": [float(row[1]) for row in category_rows],
            },
        },
        "insights": insights,
        "raw": {
            "distance": total_distance,
            "liters": total_liters,
            "operating_cost": operating_cost,
            "revenue": revenue,
            "roi": roi,
        },
    }


@app.get("/reports")
def reports():
    selected_value = request.args.get("month", "")
    try:
        selected_month = datetime.strptime(selected_value, "%Y-%m").date() if selected_value else date.today()
    except ValueError:
        selected_month = date.today()
    data = report_data(selected_month)
    return render_template(
        "reports.html",
        page_title="Reports Analytics",
        page_subtitle="Actionable fleet insights and performance intelligence",
        stats=data["stats"],
        chart_data=data["charts"],
        insights=data["insights"],
        selected_month=selected_month.strftime("%Y-%m"),
    )


# -----------------------------------------------------------------------------
# Search, profile and settings
# -----------------------------------------------------------------------------


@app.get("/search")
def search():
    query_text = request.args.get("q", "").strip()
    results = {"vehicles": [], "drivers": [], "trips": [], "expenses": []}
    if query_text:
        results["vehicles"] = db.session.scalars(
            select(Vehicle).where(
                or_(
                    Vehicle.registration_number.ilike(f"%{query_text}%"),
                    Vehicle.model.ilike(f"%{query_text}%"),
                )
            ).limit(10)
        ).all()
        results["drivers"] = db.session.scalars(
            select(Driver).where(
                or_(Driver.name.ilike(f"%{query_text}%"), Driver.license_number.ilike(f"%{query_text}%"))
            ).limit(10)
        ).all()
        results["trips"] = db.session.scalars(
            select(Trip).where(
                or_(Trip.origin.ilike(f"%{query_text}%"), Trip.destination.ilike(f"%{query_text}%"))
            ).limit(10)
        ).all()
        results["expenses"] = db.session.scalars(
            select(Expense).where(
                or_(Expense.category.ilike(f"%{query_text}%"), Expense.description.ilike(f"%{query_text}%"))
            ).limit(10)
        ).all()
    return render_template(
        "search.html",
        page_title="Search",
        page_subtitle="Search across fleet records",
        query=query_text,
        results=results,
    )


@app.route("/profile", methods=["GET", "POST"])
def profile():
    record = db.session.scalar(select(UserProfile).limit(1))
    if not record:
        record = UserProfile()
        db.session.add(record)
        db.session.commit()

    if request.method == "POST":
        def operation():
            record.name = required_text(request.form.get("name"), "Name", 120)
            record.email = required_text(request.form.get("email"), "Email", 180)
            record.phone = (request.form.get("phone") or "").strip() or None
            record.role = required_text(request.form.get("role"), "Role", 80)

        return save_or_flash(operation, "Profile updated.", "profile")

    return render_template(
        "profile.html",
        page_title="My Profile",
        page_subtitle="Manage administrator profile information",
        profile=record,
    )


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        session["dark_theme"] = request.form.get("dark_theme") == "on"
        session["email_notifications"] = request.form.get("email_notifications") == "on"
        flash("Settings saved.", "success")
        return redirect(url_for("settings"))
    return render_template(
        "settings.html",
        page_title="Settings",
        page_subtitle="Configure your TransitOps workspace",
        email_notifications=session.get("email_notifications", True),
    )


# -----------------------------------------------------------------------------
# CSV and PDF exports
# -----------------------------------------------------------------------------


def csv_response(filename: str, headers: list[str], rows: Iterable[Iterable]):
    stream = io.StringIO()
    stream.write("\ufeff")
    writer = csv.writer(stream)
    writer.writerow(headers)
    writer.writerows(rows)
    response = Response(
        stream.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/export/<string:report_name>.csv")
def export_csv(report_name: str):
    if report_name == "dashboard":
        trips_rows = db.session.scalars(select(Trip).order_by(Trip.start_date.desc())).all()
        return csv_response(
            "transitops-dashboard-trips.csv",
            ["Trip ID", "Date", "Vehicle", "Driver", "Origin", "Destination", "Distance KM", "Revenue", "Status"],
            [
                [
                    item.id,
                    item.start_date,
                    item.vehicle.registration_number if item.vehicle else "",
                    item.driver.name if item.driver else "",
                    item.origin,
                    item.destination,
                    item.distance_km,
                    item.revenue,
                    item.status,
                ]
                for item in trips_rows
            ],
        )
    if report_name == "fuel":
        rows = db.session.scalars(select(FuelLog).order_by(FuelLog.fuel_date.desc())).all()
        return csv_response(
            "transitops-fuel.csv",
            ["Date", "Vehicle", "Driver", "Liters", "Total Cost", "Mileage", "Station", "Invoice"],
            [
                [
                    r.fuel_date,
                    r.vehicle.registration_number if r.vehicle else "",
                    r.driver.name if r.driver else "",
                    r.liters,
                    r.total_cost,
                    r.mileage_kmpl,
                    r.station,
                    r.invoice_number or "",
                ]
                for r in rows
            ],
        )
    if report_name == "expenses":
        rows = db.session.scalars(select(Expense).order_by(Expense.expense_date.desc())).all()
        return csv_response(
            "transitops-expenses.csv",
            ["Date", "Vehicle", "Category", "Description", "Amount", "Payment", "Status"],
            [[r.expense_date, r.vehicle.registration_number if r.vehicle else "", r.category, r.description, r.amount, r.payment_method, r.status] for r in rows],
        )
    if report_name == "vehicles":
        rows = db.session.scalars(select(Vehicle).order_by(Vehicle.registration_number)).all()
        return csv_response(
            "transitops-vehicles.csv",
            ["Registration", "Model", "Type", "Capacity KG", "Acquisition Cost", "Odometer KM", "Status"],
            [[r.registration_number, r.model, r.vehicle_type, r.capacity_kg, r.acquisition_cost, r.odometer_km, r.status] for r in rows],
        )
    if report_name == "drivers":
        rows = db.session.scalars(select(Driver).order_by(Driver.name)).all()
        return csv_response(
            "transitops-drivers.csv",
            ["Name", "Phone", "Email", "Licence", "Expiry", "Status"],
            [[r.name, r.phone, r.email or "", r.license_number, r.license_expiry, r.status] for r in rows],
        )
    if report_name == "trips":
        rows = db.session.scalars(select(Trip).order_by(Trip.start_date.desc())).all()
        return csv_response(
            "transitops-trips.csv",
            ["Date", "Vehicle", "Driver", "Origin", "Destination", "Distance KM", "Revenue", "Status"],
            [
                [
                    r.start_date,
                    r.vehicle.registration_number if r.vehicle else "",
                    r.driver.name if r.driver else "",
                    r.origin,
                    r.destination,
                    r.distance_km,
                    r.revenue,
                    r.status,
                ]
                for r in rows
            ],
        )
    if report_name == "maintenance":
        rows = db.session.scalars(select(Maintenance).order_by(Maintenance.service_date.desc())).all()
        return csv_response(
            "transitops-maintenance.csv",
            ["Date", "Vehicle", "Category", "Description", "Cost", "Next Service", "Status"],
            [
                [
                    r.service_date,
                    r.vehicle.registration_number if r.vehicle else "",
                    r.category,
                    r.description,
                    r.cost,
                    r.next_service_date or "",
                    r.status,
                ]
                for r in rows
            ],
        )
    abort(404)


@app.get("/reports/export.pdf")
def export_report_pdf():
    selected_value = request.args.get("month", date.today().strftime("%Y-%m"))
    try:
        selected_month = datetime.strptime(selected_value, "%Y-%m").date()
    except ValueError:
        selected_month = date.today()
    data = report_data(selected_month)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("TransitOps Fleet Analytics Report", styles["Title"]),
        Paragraph(selected_month.strftime("%B %Y"), styles["Heading2"]),
        Spacer(1, 8 * mm),
    ]
    summary_rows = [
        ["Metric", "Value"],
        ["Fuel Efficiency", data["stats"]["fuel_efficiency"]],
        ["Operational Cost", data["stats"]["operational_cost"]],
        ["Vehicle ROI", data["stats"]["vehicle_roi"]],
        ["Fleet Utilization", data["stats"]["fleet_utilization"]],
    ]
    table = Table(summary_rows, colWidths=[75 * mm, 75 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend([table, Spacer(1, 8 * mm), Paragraph("Smart Insights", styles["Heading2"])])
    for insight in data["insights"]:
        story.append(Paragraph(f"<b>{insight['title']}</b><br/>{insight['text']}", styles["BodyText"]))
        story.append(Spacer(1, 3 * mm))
    doc.build(story)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"transitops-report-{selected_value}.pdf",
        mimetype="application/pdf",
    )


# -----------------------------------------------------------------------------
# JSON APIs for future integrations
# -----------------------------------------------------------------------------


@app.get("/api/dashboard")
def api_dashboard():
    return jsonify(
        {
            "vehicles": db.session.scalar(select(func.count(Vehicle.id))) or 0,
            "drivers": db.session.scalar(select(func.count(Driver.id))) or 0,
            "trips": db.session.scalar(select(func.count(Trip.id))) or 0,
            "expenses": float(db.session.scalar(select(func.coalesce(func.sum(Expense.amount), 0))) or 0),
        }
    )


@app.get("/api/fuel")
def api_fuel():
    rows = db.session.scalars(select(FuelLog).order_by(FuelLog.fuel_date.desc()).limit(100)).all()
    return jsonify(
        [
            {
                "id": row.id,
                "date": row.fuel_date.isoformat(),
                "vehicle": row.vehicle.registration_number,
                "driver": row.driver.name if row.driver else None,
                "liters": float(row.liters),
                "total_cost": float(row.total_cost),
                "mileage_kmpl": float(row.mileage_kmpl),
                "station": row.station,
            }
            for row in rows
        ]
    )


@app.get("/api/expenses")
def api_expenses():
    rows = db.session.scalars(select(Expense).order_by(Expense.expense_date.desc()).limit(100)).all()
    return jsonify(
        [
            {
                "id": row.id,
                "date": row.expense_date.isoformat(),
                "vehicle": row.vehicle.registration_number if row.vehicle else None,
                "category": row.category,
                "description": row.description,
                "amount": float(row.amount),
                "status": row.status,
            }
            for row in rows
        ]
    )


# -----------------------------------------------------------------------------
# CLI commands and demo data
# -----------------------------------------------------------------------------


@app.cli.command("init-db")
def init_db_command():
    db.create_all()
    print("TransitOps database tables created.")


@app.cli.command("reset-db")
def reset_db_command():
    db.drop_all()
    db.create_all()
    print("TransitOps database reset.")


@app.cli.command("seed-demo")
def seed_demo_command():
    seed_demo_data()
    print("TransitOps demo data inserted.")


def seed_demo_data() -> None:
    db.create_all()
    if db.session.scalar(select(func.count(Vehicle.id))) or 0:
        return

    random.seed(42)
    profile = UserProfile(
        name="Admin",
        email="admin@transitops.local",
        phone="+91 98765 43210",
        role="Fleet Manager",
    )
    db.session.add(profile)

    vehicle_models = [
        ("Tata Ultra", "Heavy Truck", Decimal("12000"), Decimal("2400000")),
        ("Ashok Leyland Dost", "Light Commercial", Decimal("1500"), Decimal("950000")),
        ("Mahindra Bolero Pickup", "Utility", Decimal("1700"), Decimal("1050000")),
        ("Force Traveller", "Passenger", Decimal("1100"), Decimal("1850000")),
    ]
    vehicles_seed: list[Vehicle] = []
    for index in range(48):
        model, vehicle_type, capacity, acquisition = vehicle_models[index % len(vehicle_models)]
        status = "Active" if index < 41 else ("Maintenance" if index < 45 else "Inactive")
        vehicle = Vehicle(
            registration_number=f"GJ{1 + index % 27:02d}{chr(65 + (index // 26))}{chr(65 + index % 26)}{1001 + index}",
            model=model,
            vehicle_type=vehicle_type,
            capacity_kg=capacity,
            acquisition_cost=acquisition,
            odometer_km=Decimal(str(18000 + index * 1350)),
            status=status,
        )
        vehicles_seed.append(vehicle)
        db.session.add(vehicle)

    driver_names = [
        "Rohan Patel", "Mehul Shah", "Nilesh Joshi", "Amit Trivedi", "Krunal Desai",
        "Harsh Mehta", "Jayesh Parmar", "Vishal Solanki", "Dhaval Dave", "Bhavesh Rana",
        "Parth Thakkar", "Manish Chauhan", "Kalpesh Prajapati", "Sanjay Makwana",
    ]
    drivers_seed: list[Driver] = []
    for index in range(56):
        status = "Available" if index < 49 else ("Assigned" if index < 54 else "On Leave")
        driver = Driver(
            name=f"{driver_names[index % len(driver_names)]} {index + 1}",
            phone=f"+91 98{index:08d}"[-14:],
            email=f"driver{index + 1}@transitops.local",
            license_number=f"GJ-{2020 + index % 6}-{100000 + index}",
            license_expiry=date.today() + timedelta(days=15 + index * 11),
            status=status,
        )
        drivers_seed.append(driver)
        db.session.add(driver)

    db.session.flush()

    cities = ["Ahmedabad", "Vadodara", "Rajkot", "Surat", "Bharuch", "Gandhinagar", "Mehsana", "Anand"]
    trips_seed: list[Trip] = []
    for index in range(72):
        start = date.today() - timedelta(days=index * 3)
        origin = cities[index % len(cities)]
        destination = cities[(index + 1 + index % 3) % len(cities)]
        status = "Completed" if index > 4 else (["Scheduled", "In Transit", "Completed"][index % 3])
        distance = Decimal(str(70 + (index * 17) % 280))
        trip = Trip(
            vehicle_id=vehicles_seed[index % len(vehicles_seed)].id,
            driver_id=drivers_seed[index % len(drivers_seed)].id,
            origin=origin,
            destination=destination,
            start_date=start,
            end_date=start + timedelta(days=1) if status == "Completed" else None,
            distance_km=distance,
            revenue=distance * Decimal("72"),
            status=status,
        )
        trips_seed.append(trip)
        db.session.add(trip)

    db.session.flush()

    stations = ["IndianOil - SG Highway", "HP - Naroda", "BPCL - Surat", "Shell - Gandhinagar", "Nayara - Changodar"]
    for index in range(110):
        vehicle = vehicles_seed[index % len(vehicles_seed)]
        trip = trips_seed[index % len(trips_seed)]
        liters = Decimal(str(48 + (index * 7) % 58))
        rate = Decimal(str(94 + (index % 6)))
        fuel_date = date.today() - timedelta(days=index * 2)
        log = FuelLog(
            vehicle_id=vehicle.id,
            driver_id=trip.driver_id,
            trip_id=trip.id,
            fuel_date=fuel_date,
            liters=liters,
            total_cost=(liters * rate).quantize(Decimal("0.01")),
            odometer_km=Decimal(vehicle.odometer_km or 0) + Decimal(str(index * 82)),
            mileage_kmpl=Decimal(str(10.5 + (index % 9) * 0.48)),
            station=stations[index % len(stations)],
            invoice_number=f"FUEL-{fuel_date:%Y%m}-{1000 + index}",
        )
        db.session.add(log)
        db.session.flush()
        sync_generated_expense(
            source_type="fuel",
            source_id=log.id,
            vehicle_id=log.vehicle_id,
            expense_date=log.fuel_date,
            amount=log.total_cost,
            description=f"Fuel refill at {log.station}",
        )

    maintenance_categories = ["Engine Service", "Tyre Replacement", "Oil Change", "Brake Service", "Electrical Repair"]
    for index in range(36):
        vehicle = vehicles_seed[(index * 3) % len(vehicles_seed)]
        service_date = date.today() - timedelta(days=index * 6)
        cost = Decimal(str(5500 + (index * 2350) % 42000))
        status = "Completed" if index > 3 else ("Scheduled" if index % 2 == 0 else "In Progress")
        maintenance_record = Maintenance(
            vehicle_id=vehicle.id,
            service_date=service_date,
            category=maintenance_categories[index % len(maintenance_categories)],
            description=f"{maintenance_categories[index % len(maintenance_categories)]} for {vehicle.registration_number}",
            cost=cost,
            next_service_date=service_date + timedelta(days=90 + (index % 4) * 30),
            status=status,
        )
        db.session.add(maintenance_record)
        db.session.flush()
        sync_generated_expense(
            source_type="maintenance",
            source_id=maintenance_record.id,
            vehicle_id=vehicle.id,
            expense_date=maintenance_record.service_date,
            amount=maintenance_record.cost,
            description=maintenance_record.description,
            status="Completed" if status == "Completed" else "Pending",
        )

    manual_categories = ["Insurance", "Toll", "Other"]
    descriptions = ["Annual insurance renewal", "FASTag recharge", "Parking and permits", "GPS subscription", "Road tax"]
    payment_methods = ["UPI", "Card", "Bank Transfer", "Cash"]
    for index in range(48):
        amount = Decimal(str(2500 + (index * 1900) % 36000))
        db.session.add(
            Expense(
                vehicle_id=vehicles_seed[(index * 5) % len(vehicles_seed)].id,
                expense_date=date.today() - timedelta(days=index * 4),
                category=manual_categories[index % len(manual_categories)],
                description=descriptions[index % len(descriptions)],
                amount=amount,
                payment_method=payment_methods[index % len(payment_methods)],
                status="Completed" if index % 5 else "Pending",
                source_type="manual",
            )
        )

    db.session.commit()


# -----------------------------------------------------------------------------
# Error handlers and startup
# -----------------------------------------------------------------------------


@app.errorhandler(404)
def not_found(error):
    return render_template(
        "error.html",
        page_title="Page Not Found",
        page_subtitle="The requested resource does not exist",
        error_code=404,
        error_message="The page or record you requested could not be found.",
    ), 404


@app.errorhandler(500)
def server_error(error):
    db.session.rollback()
    return render_template(
        "error.html",
        page_title="Application Error",
        page_subtitle="TransitOps could not complete the request",
        error_code=500,
        error_message="An unexpected error occurred. Check the terminal for details.",
    ), 500


with app.app_context():
    if app.config.get("AUTO_CREATE_TABLES", True):
        db.create_all()
        # Zero-configuration first run: show working data immediately.
        if app.config.get("AUTO_SEED", True):
            existing_vehicles = db.session.scalar(select(func.count(Vehicle.id))) or 0
            if existing_vehicles == 0:
                seed_demo_data()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)