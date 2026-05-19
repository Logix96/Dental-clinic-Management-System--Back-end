from flask import Flask

# Import các blueprint từ thư mục routes
from routes.home import home_bp
from routes.auth import auth_bp
from routes.client import client_bp
from routes.dentist import dentist_bp
from routes.receptionist import receptionist_bp
from routes.admin import admin_bp

app = Flask(__name__)

app.secret_key = "nha_khoa_viet_secret_key_2026"

app.register_blueprint(home_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(client_bp)
app.register_blueprint(dentist_bp)
app.register_blueprint(receptionist_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(debug=True)
