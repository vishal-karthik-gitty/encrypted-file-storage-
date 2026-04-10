from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
from models.db import db, User, File
from encryption.aes_utils import encrypt_file, decrypt_file
from encryption.rsa_utils import generate_keys, encrypt_key, decrypt_key
import os
import boto3

# 🔥 AWS CONFIG (works both LOCAL + CLOUD)
AWS_ACCESS_KEY ="YOUR_ACCESS_KEY"
AWS_SECRET_KEY = "YOUR_SECRET_KEY"

S3_BUCKET = "secure-file-storage-project1"

s3 = boto3.client(
    's3',
    aws_access_key_id="AWS_ACCESS_KEY",
    aws_secret_access_key="AWS_SECRET_KEY",
    region_name='ap-south-1'
)

app = Flask(__name__)
app.config['SECRET_KEY'] = "secret123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# 🔥 Works in BOTH local + cloud
UPLOAD_FOLDER = "/tmp/uploads"
ENCRYPTED_FOLDER = "/tmp/encrypted_files"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()


# 🔐 LOGIN
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials ❌")
            return redirect(url_for('home'))

    return render_template("login.html")


# 📝 REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("Username already exists ❌")
            return redirect(url_for('register'))

        role = "admin" if not User.query.filter_by(role="admin").first() else "user"

        new_user = User(username=username, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash("Registered successfully ✅ Login now")
        return redirect(url_for('home'))

    return render_template("register.html")


# 🏠 DASHBOARD
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    return render_template("dashboard.html")


# 📤 UPLOAD
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    if request.method == "POST":
        file = request.files.get('file')

        if not file or file.filename == "":
            flash("No file selected ❌")
            return redirect(url_for('upload'))

        import time
        unique_name = str(int(time.time())) + "_" + file.filename

        filepath = os.path.join(UPLOAD_FOLDER, unique_name)
        file.save(filepath)

        encrypted_path = os.path.join(ENCRYPTED_FOLDER, unique_name)
        aes_key = encrypt_file(filepath, encrypted_path)

        try:
            s3.upload_file(encrypted_path, S3_BUCKET, unique_name)
        except Exception as e:
            return f"S3 Upload Failed: {str(e)}"

        public_key, private_key = generate_keys()
        encrypted_aes_key = encrypt_key(aes_key, public_key)

        new_file = File(
            filename=unique_name,
            encrypted_key=encrypted_aes_key,
            private_key=private_key.export_key(),
            user_id=session['user_id'],
            approved=False,
            requested=False
        )

        db.session.add(new_file)
        db.session.commit()

        flash("File uploaded & encrypted successfully ✅")
        return redirect(url_for('files'))

    return render_template("upload.html")


# 👑 ADMIN PANEL
@app.route("/admin")
def admin():
    if session.get('role') != "admin":
        return "Access denied ❌"

    return render_template(
        "admin.html",
        users=User.query.all(),
        files=File.query.all()
    )


# 👑 MAKE ADMIN
@app.route("/make_admin/<int:user_id>")
def make_admin(user_id):
    if session.get('role') != "admin":
        return "Access denied ❌"

    user = User.query.get(user_id)
    if user:
        user.role = "admin"
        db.session.commit()

    return redirect(url_for('admin'))


# 🔐 REQUEST ACCESS
@app.route("/request/<int:file_id>")
def request_file(file_id):
    file = File.query.get(file_id)

    if file:
        file.requested = True
        db.session.commit()
        flash("Request sent to admin 🔔")

    return redirect(url_for('files'))


# ✅ APPROVE
@app.route("/approve/<int:file_id>")
def approve(file_id):
    if session.get('role') != "admin":
        return "Access denied ❌"

    file = File.query.get(file_id)

    if file:
        file.approved = True
        file.requested = True
        db.session.commit()
        flash("File approved ✅")

    return redirect(url_for('admin'))


# 📂 FILES
@app.route("/files")
def files():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    if session.get('role') == "admin":
        user_files = File.query.all()
    else:
        user_files = File.query.filter_by(user_id=session['user_id']).all()

    return render_template("files.html", files=user_files)


# ⬇ DOWNLOAD
@app.route("/download/<filename>")
def download(filename):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    file_record = File.query.filter_by(filename=filename).first()

    if not file_record or not file_record.approved:
        return "Access not approved ❌"

    encrypted_path = os.path.join(ENCRYPTED_FOLDER, filename)
    decrypted_path = os.path.join(UPLOAD_FOLDER, "dec_" + filename)

    from Crypto.PublicKey import RSA

    # Download from S3
    s3.download_file(S3_BUCKET, filename, encrypted_path)

    private_key = RSA.import_key(file_record.private_key)
    aes_key = decrypt_key(file_record.encrypted_key, private_key)

    decrypt_file(encrypted_path, decrypted_path, aes_key)

    return send_file(decrypted_path, as_attachment=True)


# 🚪 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)