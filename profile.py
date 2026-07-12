from flask import Blueprint, render_template, session, redirect, url_for, request, flash

profile_bp = Blueprint("profile", __name__)


# =====================================
# Profile Page
# =====================================

@profile_bp.route("/profile")
def profile():

    # Check Login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = {

        "id": session.get("user_id"),
        "name": session.get("user_name"),
        "email": "admin@gmail.com",
        "phone": "9876543210",
        "role": session.get("role")

    }

    return render_template(
        "profile.html",
        user=user
    )


# =====================================
# Update Profile
# =====================================

@profile_bp.route("/profile/update", methods=["POST"])
def update_profile():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")

    # ---------------------------------
    # MySQL Update (Commented)
    # ---------------------------------
    #
    # user = User.query.get(session["user_id"])
    #
    # user.name = name
    # user.email = email
    # user.phone = phone
    #
    # db.session.commit()
    #
    # ---------------------------------

    # Temporary Session Update

    session["user_name"] = name

    flash("Profile Updated Successfully", "success")

    return redirect(url_for("profile.profile"))