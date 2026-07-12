from flask import Flask
from routes.vehicle import vehicle_bp
from routes.driver import driver_bp

app = Flask(__name__)

app.secret_key = "transitops_secret_key"

# Register Blueprint
app.register_blueprint(vehicle_bp)
app.register_blueprint(driver_bp)

# Uncomment when using MySQL
"""
from database.db import db

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:password@localhost/transitops"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()
"""

print(app.url_map)      

if __name__ == "__main__":
    app.run(debug=True)