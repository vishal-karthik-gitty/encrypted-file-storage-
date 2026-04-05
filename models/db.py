from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100))
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")  # ✅ NEW

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    encrypted_key = db.Column(db.LargeBinary)
    private_key = db.Column(db.LargeBinary)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    approved = db.Column(db.Boolean, default=False)
    requested = db.Column(db.Boolean, default=False)

