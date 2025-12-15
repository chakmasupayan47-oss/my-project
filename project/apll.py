from flask import Flask, render_template, request, redirect, url_for, session, flash
import pickle
import numpy as np
import pandas as pd
import os
import json
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'
app.config['SESSION_TYPE'] = 'filesystem'

# Database setup
def init_db():
    conn = sqlite3.connect('cancer-risk-factors.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            patient_id INTEGER,
            prediction INTEGER,
            probability REAL,
            features TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Load ML model
try:
    load_model = pickle.load(open("svm_model_for_cancer.sav", "rb"))
    scaler = pickle.load(open("scaler.pkl", "rb")) if os.path.exists("scaler.pkl") else None
    print("Model loaded successfully")
except Exception as e:
    print(f" Error loading model: {e}")
    load_model = None

# Encoding maps
gender_map = {"Male": 1, "Female": 0}
smoking_map = {"Current Smoker": 2, "Former Smoker": 1, "Never Smoked": 0}
yes_no_map = {"Yes": 1, "No": 0}
obesity_map = {"Obese": 2, "Overweight": 1, "Normal": 0}
family_map = {"Present": 1, "Absent": 0}
level_map = {"High": 2, "Moderate": 1, "Low": 0}
brca_map = {"Positive": 1, "Negative": 0}
pylori_map = {"Positive": 1, "Negative": 0}

# ==================== ROUTES ====================

try:
    load_model = pickle.load(open("svm_model_for_cancer.sav", "rb"))
    scaler = pickle.load(open("scaler.pkl", "rb")) if os.path.exists("scaler.pkl") else None
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    load_model = None

@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration"""
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form.get("confirm_password", "")
        
        # Validation
        if not name or not email or not password:
            flash("All fields are required", "danger")
            return render_template("register.html")
        
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return render_template("register.html")
        
        if len(password) < 6:
            flash("Password must be at least 6 characters", "danger")
            return render_template("register.html")
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('cancer-risk-factors.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password, name) VALUES (?, ?, ?)",
                (email, hashed_password, name)
            )
            conn.commit()
            conn.close()
            
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        
        except sqlite3.IntegrityError:
            flash("Email already registered!", "danger")
    
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    """User dashboard"""
    if "user" not in session:
        return redirect(url_for("login"))
    
    return render_template("main.html", username=session.get("user_name", session["user"]))

@app.route("/prediction-form", methods=["GET"])
def prediction_form():
    """Show prediction form"""
    if "user" not in session:
        return redirect(url_for("login"))
    
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    """Process prediction"""
    if "user" not in session:
        return redirect(url_for("login"))
    
    # Process form submission
    try:
        # ----- Read and encode user input -----
        Patient_ID = int(request.form["Patient_ID"])
        Age = float(request.form["Age"])
        Gender = gender_map[request.form["Gender"]]
        Smoking = smoking_map[request.form["Smoking"]]
        Alcohol = yes_no_map[request.form["Alcohol_Use"]]
        Obesity = obesity_map[request.form["Obesity"]]
        Family = family_map[request.form["Family_History"]]
        Diet = level_map[request.form["Diet_Red_Meat"]]
        Salted = level_map[request.form["Diet_Salted_Processed"]]
        Fruit = level_map[request.form["Fruit_Veg_Intake"]]
        Physical = level_map[request.form["Physical_Activity"]]
        Pollution = level_map[request.form["Air_Pollution"]]
        Occupational = yes_no_map[request.form["Occupational_Hazards"]]
        BRCA = brca_map[request.form["BRCA_Mutation"]]
        Pylori = pylori_map[request.form["H_Pylori_Infection"]]
        Calcium = level_map[request.form["Calcium_Intake"]]
        BMI = float(request.form["BMI"])
        Activity = level_map[request.form["Physical_Activity_Level"]]
        
        # ----- Create input array -----
        input_data = np.array([[
            Patient_ID, Age, Gender, Smoking, Alcohol,
            Obesity, Family, Diet, Salted, Fruit,
            Physical, Pollution, Occupational, BRCA,
            Pylori, Calcium, BMI, Activity
        ]])
        
        # Apply scaling if scaler exists
        if scaler:
            input_data = scaler.transform(input_data)
        
        # Make prediction
        if load_model:
            prediction = int(load_model.predict(input_data)[0])
            
            # Get probability if available
            try:
                probability = float(load_model.predict_proba(input_data)[0][1])
            except:
                probability = 0.8 if prediction == 1 else 0.2
            
            # Save to database
            conn = sqlite3.connect('cancer-risk-factors.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO predictions (user_id, patient_id, prediction, probability, features)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session["user_id"],
                Patient_ID,
                prediction,
                probability,
                json.dumps(request.form.to_dict())
            ))
            conn.commit()
            conn.close()
            
            # Prepare data for template
            features_display = {
                'age': Age,
                'bmi': BMI,
                'gender': request.form["Gender"],
                'smoking_display': request.form["Smoking"],
                'family_history_display': request.form["Family_History"],
                'alcohol': request.form["Alcohol_Use"],
                'obesity': request.form["Obesity"],
                'diet': request.form["Diet_Red_Meat"],
                'physical_activity': request.form["Physical_Activity_Level"],
                'occupational': request.form["Occupational_Hazards"]
            }
            
            return render_template("result.html",
                                 prediction=prediction,
                                 probability=probability,
                                 features=features_display,
                                 patient_id=Patient_ID)
        else:
            flash("Model not loaded. Please contact administrator.", "danger")
            return redirect(url_for("prediction_form"))
    
    except KeyError as e:
        flash(f"Missing field: {str(e)}", "danger")
        return redirect(url_for("prediction_form"))
    except ValueError as e:
        flash(f"Invalid input format: {str(e)}", "danger")
        return redirect(url_for("prediction_form"))
    except Exception as e:
        flash(f"Error in prediction: {str(e)}", "danger")
        return redirect(url_for("prediction_form"))

@app.route("/history")
def history():
    """Show prediction history"""
    if "user" not in session:
        return redirect(url_for("login"))
    
    conn = sqlite3.connect('cancer-risk-factors.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT patient_id, prediction, probability, created_at 
        FROM predictions 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (session["user_id"],))
    
    history_data = cursor.fetchall()
    conn.close()
    
    return render_template("history.html", history=history_data)

@app.route("/logout")
def logout():
    """Logout user"""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
    
    
    
    from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import pickle
import json
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash

# --- Config ---
app = Flask(__name__)
app.secret_key = "replace-this-with-a-secure-secret"
DB_PATH = "users.db"

# --- Database init ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        patient_id INTEGER,
        prediction INTEGER,
        probability REAL,
        features TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Load model (if exists) ---
load_model = None
scaler = None
MODEL_PATH = "svm_model_for_cancer.sav"
SCALER_PATH = "scaler.pkl"
if os.path.exists(MODEL_PATH):
    try:
        load_model = pickle.load(open(MODEL_PATH, "rb"))
        print("Model loaded successfully")
    except Exception as e:
        print("Error loading model:", e)
else:
    print("Model file not found, prediction will be disabled until you add svm_model_for_cancer.sav")

if os.path.exists(SCALER_PATH):
    try:
        scaler = pickle.load(open(SCALER_PATH, "rb"))
        print("Scaler loaded")
    except Exception as e:
        print("Couldn't load scaler:", e)

# --- Helpers ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def current_user():
    if "user_id" in session:
        return {"id": session["user_id"], "name": session.get("user_name")}
    return None

# --- Routes ---
@app.route("/")
def home():
    user = current_user()
    return render_template("home.html", user=user)

@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("All fields are required", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters", "danger")
            return render_template("register.html")

        hashed = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hashed))
            conn.commit()
            conn.close()
            flash("Registration successful — please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "danger")
            return render_template("register.html")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # if already logged in, send to admin/dashboard
    if "user_id" in session:
        return redirect(url_for("admin"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, password FROM users WHERE email = ?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            flash("Logged in successfully.", "success")
            return redirect(url_for("admin"))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("home"))

@app.route("/admin")
def admin():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    # show latest 20 predictions for this user
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT patient_id, prediction, probability, created_at FROM predictions WHERE user_id = ? ORDER BY created_at DESC LIMIT 50", (session["user_id"],))
    history = cur.fetchall()
    conn.close()

    return render_template("admin.html", history=history, user_name=session.get("user_name"))

@app.route("/predict-form")
def predict_form():
    # protected: user must be logged in
    if "user_id" not in session:
        flash("Please login to access the prediction form.", "warning")
        return redirect(url_for("login"))
    return render_template("main.html")   # main.html contains the full form

@app.route("/predict", methods=["POST"])
def predict():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    if load_model is None:
        flash("Model not loaded on server. Prediction unavailable.", "danger")
        return redirect(url_for("predict_form"))

    try:
        # --- Encoding maps (same as earlier) ---
        gender_map = {"Male": 1, "Female": 0}
        smoking_map = {"Current Smoker": 2, "Former Smoker": 1, "Never Smoked": 0}
        yes_no_map = {"Yes": 1, "No": 0}
        obesity_map = {"Obese": 2, "Overweight": 1, "Normal": 0}
        family_map = {"Present": 1, "Absent": 0}
        level_map = {"High": 2, "Moderate": 1, "Low": 0}
        brca_map = {"Positive": 1, "Negative": 0}
        pylori_map = {"Positive": 1, "Negative": 0}

        # --- Read fields from form (use .get to avoid KeyError)
        patient_id = int(request.form.get("Patient_ID", "0") or 0)
        age = float(request.form.get("Age", "0") or 0)
        gender = gender_map.get(request.form.get("Gender", "Female"), 0)
        smoking = smoking_map.get(request.form.get("Smoking", "Never Smoked"), 0)
        alcohol = yes_no_map.get(request.form.get("Alcohol_Use", "No"), 0)
        obesity = obesity_map.get(request.form.get("Obesity", "Normal"), 0)
        family = family_map.get(request.form.get("Family_History", "Absent"), 0)
        diet = level_map.get(request.form.get("Diet_Red_Meat", "Low"), 0)
        salted = level_map.get(request.form.get("Diet_Salted_Processed", "Low"), 0)
        fruit = level_map.get(request.form.get("Fruit_Veg_Intake", "Low"), 0)
        physical = level_map.get(request.form.get("Physical_Activity", "Low"), 0)
        pollution = level_map.get(request.form.get("Air_Pollution", "Low"), 0)
        occupational = yes_no_map.get(request.form.get("Occupational_Hazards", "No"), 0)
        brca = brca_map.get(request.form.get("BRCA_Mutation", "Negative"), 0)
        pylori = pylori_map.get(request.form.get("H_Pylori_Infection", "Negative"), 0)
        calcium = level_map.get(request.form.get("Calcium_Intake", "Low"), 0)
        bmi = float(request.form.get("BMI", "0") or 0)
        activity = level_map.get(request.form.get("Physical_Activity_Level", "Low"), 0)

        # --- Build feature array (must match model training order) ---
        features = [
            patient_id, age, gender, smoking, alcohol,
            obesity, family, diet, salted, fruit,
            physical, pollution, occupational, brca,
            pylori, calcium, bmi, activity
        ]
        X = np.array([features], dtype=float)

        # apply scaler if available
        X_input = X
        if scaler is not None:
            try:
                X_input = scaler.transform(X)
            except Exception:
                X_input = X

        pred_raw = load_model.predict(X_input)[0]
        # if model returns numpy types, force to int
        prediction = int(pred_raw)

        # probability if available
        prob = None
        if hasattr(load_model, "predict_proba"):
            try:
                prob = float(max(load_model.predict_proba(X_input)[0]))
            except Exception:
                prob = None

        # map to message
        if prediction == 2:
            text = "The patient is at HIGH risk"
        elif prediction == 1:
            text = "The patient is at MEDIUM risk"
        else:
            text = "The patient is at LOW risk"

        # save to DB
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO predictions (user_id, patient_id, prediction, probability, features) VALUES (?, ?, ?, ?, ?)",
                        (session["user_id"], patient_id, prediction, prob, json.dumps(features)))
            conn.commit()
            conn.close()
        except Exception as e:
            # log but continue
            print("DB save error:", e)

        return render_template("result.html", result=prediction, result_text=text, probability=prob)

    except Exception as e:
        # debug friendly
        flash(f"Prediction failed: {e}", "danger")
        return redirect(url_for("predict_form"))

# --- Simple result route (not required but kept) ---
@app.route("/result")
def result_page():
    # shows last prediction for user
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT patient_id, prediction, probability, created_at FROM predictions WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (session["user_id"],))
    rec = cur.fetchone()
    conn.close()
    return render_template("result.html", last=rec)

# --- Run ---
if __name__ == "__main__":
    app.run(debug=True)
    
    
    
       
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                      (name, email, password))
        conn.commit()
        conn.close()
        flash("Registration successful! Please login.", "success")
        return redirect("/login")
    except:
            flash("Email already exists!", "danger")
        return redirect("/register")

