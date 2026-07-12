from database.db import db


# =====================================
# Vehicle Model
# =====================================

class Vehicle(db.Model):

    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)

    registration_number = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    model = db.Column(db.String(100))

    vehicle_type = db.Column(db.String(50))

    capacity = db.Column(db.Integer)

    odometer = db.Column(db.Integer)

    acquisition_cost = db.Column(db.Float)

    status = db.Column(db.String(30))


# =====================================
# Driver Model
# =====================================

class Driver(db.Model):

    __tablename__ = "drivers"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    license_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    phone = db.Column(
        db.String(15)
    )

    experience = db.Column(
        db.Integer
    )

    status = db.Column(
        db.String(30)
    )