from flask import Flask, render_template, request, redirect, url_for, session, flash
import pickle
import numpy as np
import pandas as pd
import os
from sklearn.svm import SVC
import json
from flask import session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'you-secret-key-change-this-in-production'
app.config['SESSION_TYPE'] = 'filesystem'

DB_PATH = "users.db"
#database setup
def init_db():
    conn = sqlite3.connect('users.db')
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

#db_path = "cancer-risk-factors.db"

#table_name = "cancer"

#conn = sqlite3.connect(db_path)
#df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

 
#conn.close()
#print(df)

init_db()

#load model
try:
    load_model = pickle.load(open("svm_model_for_cancer.sav", "rb"))
    scaler = pickle.load(open("scaler.pkl", "rb")) if os.path.exists("scaler.pkl") else None
    print("Model loaded successfully")
except Exception as e:
    print(f" Error loading model: {e}")
    load_model = None
    scaler = None

@app.route("/")
def home():
    return render_template("home.html")
@app.route("/chat")
def chat_page():
    return render_template("chat.html")

#@app.route("/register", methods=["GET","POST"])
#def register_page():
    #if request.method == "POST":
        #name = request.form["name"]
        #email = request.form["email"]
        #password = request.form["password"]
        #confirm_password = request.form.get("confirm_password", "")
        
        #validation
@app.route("/register", methods=["GET","POST"])
def register_page():
    if request.method == "POST":
        
        name = request.form.get("name")
        email = request.form.get("email")
        password = generate_password_hash(request.form["password"])
        confirm_password = request.form.get("confirm_password")



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
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password, name) VALUES (?, ?, ?)",
                (email, hashed_password, name)
            )
            conn.commit()
            conn.close()
            
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("main_page"))


        except Exception as e:
            # log error in console and show generic message
            print("DB error on register:", e)
            flash("Server error. Try again.", "danger")
            return render_template("register.html")
        
        except sqlite3.IntegrityError:
            flash("Email already registered!", "danger")
        return render_template("register.html")
    
    
 
    # GET request
    return render_template("register.html")

            
#def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

#def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)
        
@app.route("/admin")
def admin():
    """User dashboard"""
    if "user" not in session:
        return redirect(url_for("register_page"))
    
    return render_template("admin.html", username=session.get("user_name", session["user"]))

@app.route("/about")
def about():
    return render_template("about.html")

#register
#@app.route("/prdiction", methods=["GET", "POST"])
#def register():
    #if request.method == "POST":
        #users = load_users()

        #email = request.form["email"]
        #password = request.form["password"]

        #if email in users:
            #return "User already registered!"

        #users[email] = password
        #save_users(users)

        #return "Registration Successful! Now you can login."

    #return render_template("register.html")

#@app.route("/", methods=["POST"])
#def login():
    #users = load_users()

    #email = request.form["email"]
    #password = request.form["password"]

    #if email in users and users[email] == password:
        #session["user"] = email
        #return redirect(url_for("users"))
    #else:
        #return "You are not registered! Please register first."



#@app.route("/register")
#def register_page():
    #if "user" not in session:
       #return "Access Denied! Please login first."

    #return render_template("register.html", user=session["user"])


#@app.route("/logout")
#def logout():
    #session.pop("user", None)
    #return redirect("/main")

# Load model
#SCALER_PATH = 'scaler.pkl'

#load_model = pickle.load(open("svm_model_for_cancer.sav", "rb"))
#load_model = pickle.load(open("svm_model_for_cancer.sav", "rb"))


#@app.route("/")
#def register_page():
    #return render_template("register.html")

@app.route("/main", methods=["GET","POST"])
def main_page():
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, password, FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            flash("Invalid Email!", "error")
            return redirect("/main.html")

        # password check
        user_id, user_name, stored_hash = user
        if not check_password_hash(user[3], password):
            flash("Invalid Password!", "error")
            return redirect("/main.html")
        
        # everything ok → login success
            # success -> set session and go to dashboard
        session["user_id"] = user_id
        session["user_name"] = user_name
        flash("Login successful!", "success")
        return redirect(url_for("dashboard"))
    
    
        # Email password
        if user and check_password_hash(user[3], password):
            session["user"] = user[0]
            session["user_name"] = user[2]

            return redirect(url_for("register_page"))

        else:
            flash("Error Email Error Password!", "danger")
            return render_template("main.html")

    return render_template("main.html")
    #return render_template("main.html")
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/register_page")
    return f"Welcome, {session['user']}!"


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/main_page")

@app.route("/index.html", methods=["GET", "POST"])
def index_page():
    if request.method == "POST":
        name = request.form.get("name")
        designation = request.form.get("designation")
        email = request.form.get("email")
        password = request.form.get("password")

        print(name, designation, email, password)

        return render_template("index.html", name=name)

    return render_template("index.html")

  
@app.route("/predict", methods=["POST"])
def predict():
   if request.method in ['GET','POST']:


    # ----- Encoding Maps -----
    gender_map = {"Male": 1, "Female": 0}

    smoking_map = {
        "Current Smoker": 2,
        "Former Smoker": 1,
        "Never Smoked": 0
    }

    yes_no_map = {"Yes": 1, "No": 0}

    obesity_map = {
        "Obese": 2,
        "Overweight": 1,
        "Normal": 0
    }

    family_map = {"Present": 1, "Absent": 0}

    level_map = {"High": 2, "Moderate": 1, "Low": 0}

    brca_map = {"Positive": 1, "Negative": 0}
    pylori_map = {"Positive": 1, "Negative": 0}

    cancer_type_map = {
        "Breast": 0,
        "Lung": 1,
        "Colon": 2,
        "Skin": 3,
        "Liver": 4
    }

    risk_level_map = {"Low": 0, "Medium": 1, "High": 2}

    # ----- Read User Input -----
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

    #Cancer_Type = cancer_type_map[request.form["Cancer_Type"]]
    #Risk_Level = risk_level_map[request.form["Risk_Level"]]

    # ----- Final Input Array -----
    input_data = np.array([[
        Patient_ID, 
        Age, Gender, Smoking, Alcohol,
        Obesity, Family, Diet, Salted, Fruit,
        Physical, Pollution, Occupational, BRCA,
        Pylori, Calcium, BMI, Activity, #--Cancer_Type,
        #Risk_Level
    ]])

    prediction = load_model.predict(input_data)[0]
    
    value = load_model.predict(...)
    
    if value == 2:
        output = "The patient is at HIGH risk"
    elif value == 1:
        output = "The patient is at Medium Risk"
    else:
        output = "The patient is at LOW risk"

        return render_template("result.html", result=prediction, result_text=output)


    #return render_template("result.html", result=prediction)

@app.route("/result", methods=["GET","POST"])
def result_page():
    result = request.args.get("result")
    return render_template("result.html", result=result)


       
    #gender_map = {"Male": 1, "Female": 0}
    #cancer_map = {"Breast": 0, "Lung": 1, "Colon": 2, "Skin": 3, "Liver": 4}
    #risk_map = {"Low": 0, "Medium": 1, "High": 2}
    
    #smoking_map = {
        #"Current Smoker": 2,
        #"Former Smoker": 1,
        #"Never Smoked": 0
    #}

    #Age = float(request.form['Age'])
    #Gender = gender_map[request.form['Gender']]
    #Smoking = smoking_map[request.form['Smoking']]
    #Alcohol = int(request.form['Alcohol_Use'])
    #Obesity = int(request.form['Obesity'])
    #Family = int(request.form['Family_History'])
    #Diet = int(request.form['Diet_Red_Meat'])
    #Salted = int(request.form['Diet_Salted_Processed'])
    #Fruit = int(request.form['Fruit_Veg_Intake'])
    #Physical = int(request.form['Physical_Activity'])
    #Pollution = int(request.form['Air_Pollution'])
    #Occupational = int(request.form['Occupational_Hazards'])
    #BRCA = int(request.form['BRCA_Mutation'])
    #Pylori = int(request.form['H_Pylori_Infection'])
    #Calcium = int(request.form['Calcium_Intake'])
    #BMI = int(request.form['BMI'])
    #Activity = int(request.form['Physical_Activity_Level'])

    #encoded_Cancer_Type = cancer_map[request.form['Cancer_Type']]
    #encoded_Risk_Level = risk_map[request.form['Risk_Level']]
    #encoded_Patient_ID = int(request.form['Patient_ID'])   # অথবা unnecessary হলে বাদ দেন

    #input_data = np.array([[Age, Gender, Smoking, Alcohol,
                            #Obesity, Family, Diet, Salted,
                            #Fruit, Physical, Pollution,
                            #Occupational, BRCA, Pylori,
                            #Calcium, BMI, Activity,
                            #encoded_Patient_ID,
                            #encoded_Cancer_Type,
                            #encoded_Risk_Level]])

    #prediction = load_model.predict(input_data)[0]

    #return render_template("result.html", result=prediction)#///>

    
    


if __name__ == "__main__":
    app.run(debug=True)
