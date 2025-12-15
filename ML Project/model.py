import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
import pickle
import os

def generate_synthetic_data(n_samples=10000):
    """Generate realistic synthetic cancer risk data"""
    np.random.seed(42)
    
    data = {
        'age': np.random.normal(55, 15, n_samples).clip(20, 90),
        'gender': np.random.choice([0, 1], n_samples, p=[0.5, 0.5]),
        'bmi': np.random.normal(25, 5, n_samples).clip(15, 40),
        'smoking_status': np.random.choice([0, 1, 2], n_samples, p=[0.4, 0.3, 0.3]),
        'alcohol_consumption': np.random.choice([0, 1, 2, 3], n_samples, p=[0.3, 0.4, 0.2, 0.1]),
        'physical_activity': np.random.choice([0, 1, 2, 3], n_samples, p=[0.2, 0.3, 0.3, 0.2]),
        'diet_quality': np.random.randint(1, 11, n_samples),
        'family_history': np.random.choice([0, 1, 2], n_samples, p=[0.7, 0.2, 0.1]),
        'genetic_markers': np.random.choice([0, 1, 2], n_samples, p=[0.8, 0.15, 0.05]),
        'previous_cancer': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        'chronic_conditions': np.random.choice([0, 1, 2], n_samples, p=[0.6, 0.3, 0.1])
    }
    
    df = pd.DataFrame(data)
    
    # Calculate risk score (realistic risk factors)
    risk_score = (
        df['age'] * 0.02 +
        df['bmi'] * 0.03 +
        (df['smoking_status'] == 2) * 0.25 +
        (df['smoking_status'] == 1) * 0.15 +
        df['alcohol_consumption'] * 0.08 -
        df['physical_activity'] * 0.06 -
        df['diet_quality'] * 0.04 +
        df['family_history'] * 0.15 +
        df['genetic_markers'] * 0.20 +
        df['previous_cancer'] * 0.30 +
        df['chronic_conditions'] * 0.10
    )
    
    # Add some noise
    risk_score += np.random.normal(0, 0.1, n_samples)
    
    # Convert to binary classification (20% positive class)
    threshold = np.percentile(risk_score, 80)
    df['cancer_risk'] = (risk_score > threshold).astype(int)
    
    return df

def train_model():
    """Train and save the Random Forest model"""
    print("Generating synthetic data...")
    df = generate_synthetic_data(10000)
    
    # Prepare features and target
    X = df.drop('cancer_risk', axis=1)
    y = df['cancer_risk']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest model
    print("Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features='sqrt',
        random_state=42,
        class_weight='balanced'
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    auc_score = roc_auc_score(y_test, y_pred_proba)
    
    print(f"Model Accuracy: {accuracy:.4f}")
    print(f"AUC Score: {auc_score:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save model and scaler
    with open('model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    with open('scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    
    # Save feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nFeature Importance:")
    print(feature_importance)
    
    # Save sample data for reference
    df.to_csv('cancer_risk_data.csv', index=False)
    
    print("\nModel training completed successfully!")
    return model, scaler, feature_importance

if __name__ == '__main__':
    train_model()