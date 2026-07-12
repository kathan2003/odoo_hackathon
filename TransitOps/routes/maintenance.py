from flask import Blueprint, render_template

maintenance_bp = Blueprint("maintenance", __name__)

@maintenance_bp.route("/maintenance")
def maintenance_list():
    return render_template("maintenance/maintenance_list.html")

@maintenance_bp.route("/maintenance/add")
def add_maintenance():
    return render_template("maintenance/add_maintenance.html")