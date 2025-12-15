from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import numpy as np
import pickle
import os
from model import train_model

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Load model and scaler
MODEL_PATH = 'model.pkl'
SCALER_PATH = 'scaler.pkl'

def load_model():
    """Load the trained model and scaler"""
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        with open(SCALER_PATH, 'rb') as f:
            scaler = pickle.load(f)
        return model, scaler
    except FileNotFoundError:
        print("Model not found. Training new model...")
        train_model()
        return load_model()

# Load model at startup
model, scaler = load_model()

# Feature names (must match training data)
FEATURES = [
    'age', 'gender', 'bmi', 'smoking_status', 'alcohol_consumption',
    'physical_activity', 'diet_quality', 'family_history', 
    'genetic_markers', 'previous_cancer', 'chronic_conditions'
]

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        try:
            # Get form data
            features = []
            
            # Numerical features
            features.append(float(request.form['age']))
            features.append(float(request.form['gender']))
            features.append(float(request.form['bmi']))
            features.append(float(request.form['smoking_status']))
            features.append(float(request.form['alcohol_consumption']))
            features.append(float(request.form['physical_activity']))
            features.append(float(request.form['diet_quality']))
            features.append(float(request.form['family_history']))
            features.append(float(request.form['genetic_markers']))
            features.append(float(request.form['previous_cancer']))
            features.append(float(request.form['chronic_conditions']))
            
            # Convert to numpy array
            features_array = np.array(features).reshape(1, -1)
            
            # Scale features
            features_scaled = scaler.transform(features_array)
            
            # Make prediction
            prediction = model.predict(features_scaled)[0]
            probability = model.predict_proba(features_scaled)[0][1]
            
            # Store in session for results page
            session['prediction'] = int(prediction)
            session['probability'] = float(probability)
            session['features'] = features
            
            return render_template('results.html', 
                                 prediction=prediction,
                                 probability=probability,
                                 features=dict(zip(FEATURES, features)))
            
        except Exception as e:
            return render_template('predict.html', error=str(e))
    
    return render_template('predict.html')

@app.route('/results')
def results():
    prediction = session.get('prediction', 0)
    probability = session.get('probability', 0.0)
    features = session.get('features', [])
    
    return render_template('results.html',
                         prediction=prediction,
                         probability=probability,
                         features=dict(zip(FEATURES, features)))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """API endpoint for predictions"""
    try:
        data = request.get_json()
        
        features = []
        for feature in FEATURES:
            features.append(float(data[feature]))
        
        features_array = np.array(features).reshape(1, -1)
        features_scaled = scaler.transform(features_array)
        
        prediction = model.predict(features_scaled)[0]
        probability = model.predict_proba(features_scaled)[0][1]
        
        return jsonify({
            'prediction': int(prediction),
            'probability': float(probability),
            'risk_level': 'High' if prediction == 1 else 'Low',
            'risk_percentage': round(probability * 100, 2)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/features')
def api_features():
    """Return feature information"""
    feature_info = {
        'age': {'min': 20, 'max': 90, 'description': 'Age in years'},
        'gender': {'options': {'0': 'Female', '1': 'Male'}, 'description': 'Biological sex'},
        'bmi': {'min': 15, 'max': 40, 'description': 'Body Mass Index'},
        'smoking_status': {'options': {'0': 'Never', '1': 'Former', '2': 'Current'}, 'description': 'Smoking history'},
        'alcohol_consumption': {'options': {'0': 'None', '1': 'Light', '2': 'Moderate', '3': 'Heavy'}, 'description': 'Alcohol intake'},
        'physical_activity': {'options': {'0': 'Sedentary', '1': 'Light', '2': 'Moderate', '3': 'Active'}, 'description': 'Exercise level'},
        'diet_quality': {'min': 1, 'max': 10, 'description': 'Diet quality score (1-10)'},
        'family_history': {'options': {'0': 'None', '1': 'Second-degree', '2': 'First-degree'}, 'description': 'Family cancer history'},
        'genetic_markers': {'options': {'0': 'None', '1': 'Low-risk', '2': 'High-risk'}, 'description': 'Genetic predisposition'},
        'previous_cancer': {'options': {'0': 'No', '1': 'Yes'}, 'description': 'Previous cancer diagnosis'},
        'chronic_conditions': {'options': {'0': 'None', '1': 'One', '2': 'Multiple'}, 'description': 'Chronic health conditions'}
    }
    
    return jsonify(feature_info)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)