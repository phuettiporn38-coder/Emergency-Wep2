from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///help_requests.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = "my_secret_key"   # สำหรับ session

db = SQLAlchemy(app)

# Model
class HelpRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.String(50))
    longitude = db.Column(db.String(50))
    type = db.Column(db.String(50), nullable=False)   # ประเภทที่แจ้ง
    image = db.Column(db.String(200))  # path รูป
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="pending")

# หน้าแรก
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        address = request.form["address"]
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        help_type = request.form["type"]

        # อัพโหลดรูป
        image_file = request.files["image"]
        filename = None
        if image_file and image_file.filename != "":
            filename = datetime.now().strftime("%Y%m%d%H%M%S_") + image_file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)

        new_request = HelpRequest(
            name=name, phone=phone, address=address,
            latitude=latitude, longitude=longitude,
            type=help_type, image=filename
        )
        db.session.add(new_request)
        db.session.commit()
        return redirect(url_for("success"))

    return render_template("index.html")

# success page
@app.route("/success")
def success():
    return render_template("success.html")

# login admin
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form["password"]
        if password == "1234":   # 🔑 เปลี่ยนรหัสตรงนี้
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            return render_template("login.html", error="รหัสผ่านไม่ถูกต้อง")
    return render_template("login.html")

# admin page
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    requests = HelpRequest.query.order_by(HelpRequest.created_at.desc()).all()
    return render_template("admin.html", requests=requests)

@app.route("/delete/<int:request_id>")
def delete_request(request_id):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    req = HelpRequest.query.get_or_404(request_id)
    db.session.delete(req)
    db.session.commit()
    return redirect(url_for("admin"))

@app.route("/done/<int:request_id>")
def mark_done(request_id):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    req = HelpRequest.query.get_or_404(request_id)
    req.status = "done"
    db.session.commit()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
