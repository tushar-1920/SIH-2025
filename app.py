import csv
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import Config
from models import db, User, Farm, RiskAssessment, Checklist, TrainingModule
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)

# ---------- Database Setup ----------
db.init_app(app)
migrate = Migrate(app, db)

# ---------- Login Manager ----------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))


# ---------- Routes ----------
# @app.route('/')
# def index():
#     if current_user.is_authenticated:
#         return render_template('index.html')

@app.route('/')
def index():
    return render_template('index.html')

# -------- Auth --------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        password = request.form['password']
        role = request.form.get('role','farmer')

        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('register'))

        user = User(
            name=name,
            email=email,
            role=role,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

# -------- Dashboard --------
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == "admin":
        farms = Farm.query.all()
    elif current_user.role == "vet":
        farms = current_user.farms_assigned
    else:  # farmer
        farms = current_user.farms_owned
    return render_template('dashboard.html', farms=farms)

# -------- Admin Panel --------
@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))

    farms = Farm.query.all()
    users = User.query.all()
    return render_template('admin.html', farms=farms, users=users)

@app.route("/admin/add_farm", methods=["GET", "POST"])
@login_required
def admin_add_farm():
    if current_user.role != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    farmers = User.query.filter_by(role="farmer").all()
    vets = User.query.filter_by(role="vet").all()

    if request.method == "POST":
        name = request.form.get("name")
        location = request.form.get("location")
        animal_count = request.form.get("animal_count", type=int)
        farmer_id = request.form.get("farmer_id")
        vet_id = request.form.get("vet_id")

        if not farmer_id:
            flash("You must select a farmer!", "danger")
            return redirect(url_for("admin_add_farm"))

        farm = Farm(
            name=name,
            location=location,
            animal_count=animal_count,
            farmer_id=farmer_id,
            vet_id=vet_id
        )
        db.session.add(farm)
        db.session.commit()

        flash("Farm added successfully!", "success")
        return redirect(url_for("admin"))

    return render_template("admin_add_farm.html", farmers=farmers, vets=vets)

@app.route('/admin/export')
@login_required
def export_csv():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    farms = Farm.query.all()
    filename = 'export.csv'
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Farm','Farmer','Vet','Location','Animals'])
        for farm in farms:
            farmer = farm.farmer.name if farm.farmer else "Unassigned"
            vet = farm.vet.name if farm.vet else "Unassigned"
            writer.writerow([farm.name, farmer, vet, farm.location, farm.animal_count])
    return f"Exported {len(farms)} farms to {filename}"


# -------- Farms --------
# -------- New Farm --------
@app.route('/farm/new', methods=['GET', 'POST'])
@login_required
def new_farm():
    if current_user.role != 'admin':
        flash("Only admins can create farms", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        animal_count = int(request.form['animal_count'])
        farmer_id = request.form['farmer_id']
        vet_id = request.form.get('vet_id')

        farm = Farm(
            name=name,
            location=location,
            animal_count=animal_count,
            farmer_id=farmer_id,
            vet_id=vet_id
        )
        db.session.add(farm)
        db.session.commit()
        flash('Farm created successfully', 'success')
        return redirect(url_for('dashboard'))

    farmers = User.query.filter_by(role='farmer').all()
    vets = User.query.filter_by(role='vet').all()
    return render_template('new_farm.html', farmers=farmers, vets=vets)


# -------- View Farm --------
@app.route('/farm/<int:farm_id>')
@login_required
def view_farm(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    print(f"DEBUG: Viewing farm {farm.id} - {farm.name}")

    # Access control for risk reports & checklists
    if current_user.role == 'admin':
        risk_reports = RiskAssessment.query.filter_by(farm_id=farm_id).all()
        checklists = Checklist.query.filter_by(farm_id=farm_id).all()
    elif current_user.role == 'vet' and farm.vet_id == current_user.id:
        risk_reports = RiskAssessment.query.filter_by(farm_id=farm_id, user_id=current_user.id).all()
        checklists = Checklist.query.filter_by(farm_id=farm_id, user_id=current_user.id).all()
    elif current_user.role == 'farmer' and farm.farmer_id == current_user.id:
        risk_reports = RiskAssessment.query.filter_by(farm_id=farm_id, user_id=current_user.id).all()
        checklists = Checklist.query.filter_by(farm_id=farm_id, user_id=current_user.id).all()
    else:
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))

    print(f"DEBUG: risk_reports={risk_reports}")
    print(f"DEBUG: checklists={checklists}")

    return render_template('view_farm.html', farm=farm, risk_reports=risk_reports, checklists=checklists)


# -------- Risk Assessment --------
@app.route('/farm/<int:farm_id>/risk', methods=['GET', 'POST'])
@login_required
def risk_assessment(farm_id):
    farm = Farm.query.get_or_404(farm_id)

    # Only farmer (owner) or assigned vet can do this
    if current_user.role == 'farmer' and farm.farmer_id != current_user.id:
        return "Unauthorized", 403
    if current_user.role == 'vet' and farm.vet_id != current_user.id:
        return "Unauthorized", 403

    if request.method == 'POST':
        q1 = int(request.form['q1'])
        q2 = int(request.form['q2'])
        q3 = int(request.form['q3'])
        notes = request.form.get('notes', '')
        score = q1 + q2 + q3
        level = 'Low' if score <= 5 else 'Medium' if score <= 10 else 'High'

        ra = RiskAssessment(
            farm_id=farm.id,
            user_id=current_user.id,  # ✅ Save which user created this assessment
            score=score,
            level=level,
            notes=notes
        )
        db.session.add(ra)
        db.session.commit()

        if level == 'High':
            print(f"🚨 ALERT: High risk detected for {farm.name}")  # placeholder for SMS/Email

        flash(f'Assessment saved — {level} risk', 'success')
        return redirect(url_for('view_farm', farm_id=farm.id))

    return render_template('risk_assessment.html', farm=farm)


# -------- Checklist --------
@app.route('/farm/<int:farm_id>/checklist', methods=['GET', 'POST'])
@login_required
def checklist(farm_id):
    farm = Farm.query.get_or_404(farm_id)

    # Only farmer (owner) or assigned vet can do this
    if current_user.role == 'farmer' and farm.farmer_id != current_user.id:
        return "Unauthorized", 403
    if current_user.role == 'vet' and farm.vet_id != current_user.id:
        return "Unauthorized", 403

    if request.method == 'POST':
        hygiene = bool(request.form.get('hygiene'))
        feed = bool(request.form.get('feed'))
        visitor = bool(request.form.get('visitor'))

        total = sum([hygiene, feed, visitor])
        compliance = round((total / 3) * 100, 2)

        cl = Checklist(
            farm_id=farm.id,
            user_id=current_user.id,   # ✅ Now linked to logged-in user
            hygiene=hygiene,
            feed_quality=feed,
            visitor_control=visitor,
            compliance=compliance
        )
        db.session.add(cl)
        db.session.commit()

        flash(f'Checklist saved — Compliance {compliance}%', 'success')
        return redirect(url_for('view_farm', farm_id=farm.id))

    return render_template('checklist.html', farm=farm)





# -------- CLI for Init --------
@app.cli.command('init-db')
def init_db():
    db.create_all()
    print("DB tables created!")

# -------- Run --------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
