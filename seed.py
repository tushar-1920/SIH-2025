from app import app, db
from models import User, Farm, RiskAssessment, Checklist, TrainingModule
from werkzeug.security import generate_password_hash
from datetime import datetime


def seed_data():
    with app.app_context():
        # Drop and recreate tables (only for development/demo)
        db.drop_all()
        db.create_all()

        # --- Users ---
        admin = User(
            name="Admin User",
            email="admin@example.com",
            password_hash=generate_password_hash("admin123"),
            role="admin"
        )
        farmer = User(
            name="Farmer Ram",
            email="farmer@example.com",
            password_hash=generate_password_hash("farmer123"),
            role="farmer"
        )

        db.session.add_all([admin, farmer])
        db.session.commit()

        # --- Farms ---
        farm1 = Farm(
            name="Green Valley Farm",
            location="Punjab",
            animal_count=120,
            farmer=farmer   # ✅ use relationship name instead of "owner"
        )
        farm2 = Farm(
            name="Sunrise Dairy",
            location="Karnataka",
            animal_count=80,
            farmer=farmer   # ✅ corrected
        )
        db.session.add_all([farm1, farm2])
        db.session.commit()

        # --- Risk Assessments ---
        ra1 = RiskAssessment(
            farm=farm1,
            score=85,
            level="Medium",
            notes="Need better visitor control"
        )
        ra2 = RiskAssessment(
            farm=farm2,
            score=95,
            level="Low",
            notes="Farm practices are excellent"
        )
        db.session.add_all([ra1, ra2])
        db.session.commit()

        # --- Checklists ---
        checklist1 = Checklist(
            farm=farm1,
            hygiene=True,
            feed_quality=False,
            visitor_control=True,
            compliance=66.7
        )
        checklist2 = Checklist(
            farm=farm2,
            hygiene=True,
            feed_quality=True,
            visitor_control=True,
            compliance=100.0
        )
        db.session.add_all([checklist1, checklist2])
        db.session.commit()

        # --- Training Modules ---
        module1 = TrainingModule(
            title="Farm Hygiene Basics",
            description="Learn best practices to keep animals healthy.",
            url="https://example.com/hygiene.pdf"
        )
        module2 = TrainingModule(
            title="Modern Feeding Techniques",
            description="Improve animal nutrition with modern feeding methods.",
            url="https://example.com/feeding.mp4"
        )
        db.session.add_all([module1, module2])
        db.session.commit()

        print("✅ Database seeded with demo data!")


if __name__ == "__main__":
    seed_data()
