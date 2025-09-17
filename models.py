from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# -----------------------
# User Model
# -----------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(30), default="farmer")

    # Relationships
    farms_owned = db.relationship("Farm", foreign_keys="Farm.farmer_id", backref="farmer", lazy=True)
    farms_assigned = db.relationship("Farm", foreign_keys="Farm.vet_id", backref="vet", lazy=True)


# -----------------------
# Farm Model
# -----------------------
class Farm(db.Model):
    __tablename__ = "farms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(255))
    animal_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Owner (Farmer)
    farmer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Assigned vet (one vet per farm for simplicity)
    vet_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    risk_assessments = db.relationship("RiskAssessment", backref="farm", cascade="all, delete-orphan", lazy=True)
    checklists = db.relationship("Checklist", backref="farm", cascade="all, delete-orphan", lazy=True)


# -----------------------
# Risk Assessment Model
# -----------------------
class RiskAssessment(db.Model):
    __tablename__ = "risk_assessments"

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)  # Add this line

    score = db.Column(db.Integer, nullable=False)
    level = db.Column(db.String(50), nullable=False)  # Low, Medium, High
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")  # Add this line

    def __repr__(self):
        return f"<RiskAssessment {self.level} - {self.score}>"


# -----------------------
# Checklist Model
# -----------------------
class Checklist(db.Model):
    __tablename__ = "checklists"

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    hygiene = db.Column(db.Boolean, default=False)
    feed_quality = db.Column(db.Boolean, default=False)
    visitor_control = db.Column(db.Boolean, default=False)
    compliance = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="checklists")

   

# -----------------------
# Training Module Model
# -----------------------
class TrainingModule(db.Model):
    __tablename__ = "training_modules"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(300))  # PDF/Video link
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TrainingModule {self.title}>"
