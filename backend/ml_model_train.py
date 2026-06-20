import json
import os
import pickle
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
DATASET_URL = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.csv"
DATASET_FILE = str(PROJECT_ROOT / "pima-indians-diabetes.csv")
MODEL_FILE = str(BACKEND_DIR / "diabetes_model.pkl")
SCALER_FILE = str(BACKEND_DIR / "scaler.pkl")
MEDIANS_FILE = str(BACKEND_DIR / "feature_medians.json")
ZERO_FIELDS = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]

def download_data():
    if not os.path.exists(DATASET_FILE):
        print(f"Downloading dataset from {DATASET_URL}...")
        urllib.request.urlretrieve(DATASET_URL, DATASET_FILE)
        print("Download complete.")
    else:
        print("Dataset already exists locally.")

def train_model():
    # Load dataset
    column_names = [
        "Pregnancies", "Glucose", "BloodPressure", "SkinThickness", 
        "Insulin", "BMI", "DiabetesPedigreeFunction", "Age", "Outcome"
    ]
    df = pd.read_csv(DATASET_FILE, names=column_names)
    
    # Simple data cleaning: replace 0 in specific columns with median
    feature_medians = {}
    for field in ZERO_FIELDS:
        df[field] = df[field].replace(0, np.nan)
        feature_medians[field] = float(df[field].median())
        df[field] = df[field].fillna(feature_medians[field])
        
    # Split into features (X) and target (y)
    X = df.drop("Outcome", axis=1)
    y = df["Outcome"]
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest Classifier
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=8, min_samples_split=4)
    model.fit(X_train_scaled, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Training Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save the model, scaler, and imputation medians used at inference time
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model, f)
    with open(SCALER_FILE, "wb") as f:
        pickle.dump(scaler, f)
    with open(MEDIANS_FILE, "w", encoding="utf-8") as f:
        json.dump(feature_medians, f, indent=2)

    print(f"Saved model to {MODEL_FILE}")
    print(f"Saved scaler to {SCALER_FILE}")
    print(f"Saved feature medians to {MEDIANS_FILE}")
    
    # Test loading
    with open(MODEL_FILE, 'rb') as f:
        loaded_model = pickle.load(f)
    print("Self-test load successful.")

if __name__ == "__main__":
    download_data()
    train_model()
