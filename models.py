from datetime import datetime
from database.db import db


# ==========================================================
# User Model (Temporary for Local Development)
# ==========================================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)


# ==========================================================
# Vehicle Model
# (Temporary until Member 2 merges)
# ==========================================================

class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)

    registration_number = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    model = db.Column(
        db.String(100),
        nullable=False,
        default="Unknown"
    )

    vehicle_type = db.Column(
        db.String(50),
        nullable=False,
        default="Truck"
    )

    capacity = db.Column(
        db.Float,
        nullable=False,
        default=1000
    )

    odometer = db.Column(
        db.Float,
        default=0
    )

    acquisition_cost = db.Column(
        db.Float,
        default=0
    )

    status = db.Column(
        db.String(30),
        default="Available"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Vehicle {self.registration_number}>"

    def to_dict(self):
        return {
            "id": self.id,
            "registration_number": self.registration_number,
            "model": self.model,
            "vehicle_type": self.vehicle_type,
            "capacity": self.capacity,
            "odometer": self.odometer,
            "acquisition_cost": self.acquisition_cost,
            "status": self.status
        }


# ==========================================================
# Trip Model
# (Temporary until Member 3 merges)
# ==========================================================

class Trip(db.Model):
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)

    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey("vehicles.id")
    )

    source = db.Column(db.String(100))
    destination = db.Column(db.String(100))

    distance = db.Column(
        db.Float,
        default=0
    )

    revenue = db.Column(
        db.Float,
        default=0
    )

    status = db.Column(
        db.String(30),
        default="Completed"
    )

    vehicle = db.relationship(
        "Vehicle",
        backref="trips"
    )

    def __repr__(self):
        return f"<Trip {self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "source": self.source,
            "destination": self.destination,
            "distance": self.distance,
            "revenue": self.revenue,
            "status": self.status
        }


# ==========================================================
# Fuel Log Model
# ==========================================================

class FuelLog(db.Model):
    __tablename__ = "fuel_logs"

    id = db.Column(db.Integer, primary_key=True)

    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey("vehicles.id"),
        nullable=False
    )

    trip_id = db.Column(
        db.Integer,
        db.ForeignKey("trips.id"),
        nullable=True
    )

    fuel_liters = db.Column(
        db.Float,
        nullable=False
    )

    fuel_cost = db.Column(
        db.Float,
        nullable=False
    )

    fuel_station = db.Column(
        db.String(100)
    )

    fuel_date = db.Column(
        db.Date,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    vehicle = db.relationship(
        "Vehicle",
        backref="fuel_logs"
    )

    trip = db.relationship(
        "Trip",
        backref="fuel_logs"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "trip_id": self.trip_id,
            "fuel_liters": self.fuel_liters,
            "fuel_cost": self.fuel_cost,
            "fuel_station": self.fuel_station,
            "fuel_date": str(self.fuel_date)
        }


# ==========================================================
# Expense Model
# ==========================================================

class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)

    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey("vehicles.id"),
        nullable=False
    )

    expense_type = db.Column(
        db.String(50),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    expense_date = db.Column(
        db.Date,
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    vehicle = db.relationship(
        "Vehicle",
        backref="expenses"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "expense_type": self.expense_type,
            "amount": self.amount,
            "expense_date": str(self.expense_date),
            "description": self.description
        }