from flask import Blueprint, render_template, request, redirect, url_for, session, flash

auth_bp = Blueprint("auth", __name__)


# ==========================
# Login
# ==========================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        # Temporary Login
        if email == "admin@gmail.com" and password == "1234":

            session["user_id"] = 1
            session["user_name"] = "Devvrat Vyas"
            session["role"] = "Fleet Manager"

            return redirect(url_for("dashboard.dashboard"))

        flash("Invalid Email or Password", "danger")

    return render_template("login.html")


# ==========================
# Register
# ==========================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if password != confirm:
            flash("Passwords do not match", "danger")
            return redirect(url_for("auth.register"))

        flash("Registration Successful (Demo)", "success")
        return redirect(url_for("auth.login"))

    return render_template("registration.html")