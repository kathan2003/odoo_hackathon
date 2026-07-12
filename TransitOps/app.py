from flask import Flask, render_template
from routes.trip import trip_bp
from routes.maintenance import maintenance_bp

app = Flask(__name__)

app.register_blueprint(trip_bp)
app.register_blueprint(maintenance_bp)

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)