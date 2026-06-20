import json
import os
import pickle
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

FEATURE_COLUMNS = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
]

# Medians from Pima training set (zeros treated as missing before computing)
DEFAULT_MEDIANS = {
    "Glucose": 117.0,
    "BloodPressure": 72.0,
    "SkinThickness": 29.0,
    "Insulin": 125.0,
    "BMI": 32.3,
}

MODEL_FILENAME = "diabetes_model.pkl"
SCALER_FILENAME = "scaler.pkl"
MEDIANS_FILENAME = "feature_medians.json"

model = None
scaler = None
feature_medians = dict(DEFAULT_MEDIANS)
positive_class_index = 1


def _artifact_paths() -> list[Path]:
    return [
        BACKEND_DIR / MODEL_FILENAME,
        PROJECT_ROOT / MODEL_FILENAME,
    ]


def _scaler_paths() -> list[Path]:
    return [
        BACKEND_DIR / SCALER_FILENAME,
        PROJECT_ROOT / SCALER_FILENAME,
    ]


def _medians_paths() -> list[Path]:
    return [
        BACKEND_DIR / MEDIANS_FILENAME,
        PROJECT_ROOT / MEDIANS_FILENAME,
    ]


def _load_json_medians() -> None:
    global feature_medians
    for path in _medians_paths():
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                feature_medians = {**DEFAULT_MEDIANS, **json.load(f)}
            return


def _ensure_model_artifacts() -> None:
    model_path = next((p for p in _artifact_paths() if p.exists()), None)
    scaler_path = next((p for p in _scaler_paths() if p.exists()), None)
    if model_path and scaler_path:
        return

    print("ML model artifacts not found. Training model now (first run)...")
    from backend.ml_model_train import train_model

    train_model()


def load_models() -> Tuple[Optional[object], Optional[object]]:
    global model, scaler, positive_class_index

    _load_json_medians()

    try:
        _ensure_model_artifacts()
    except Exception as exc:
        print(f"Could not auto-train ML model: {exc}")

    loaded_model = None
    loaded_scaler = None

    for path in _artifact_paths():
        if path.exists():
            try:
                with open(path, "rb") as f:
                    loaded_model = pickle.load(f)
                print(f"Loaded ML model from: {path}")
                break
            except Exception as exc:
                print(f"Error loading model from {path}: {exc}")

    for path in _scaler_paths():
        if path.exists():
            try:
                with open(path, "rb") as f:
                    loaded_scaler = pickle.load(f)
                print(f"Loaded feature scaler from: {path}")
                break
            except Exception as exc:
                print(f"Error loading scaler from {path}: {exc}")

    if loaded_model is not None and hasattr(loaded_model, "classes_"):
        classes = list(loaded_model.classes_)
        if 1 in classes:
            positive_class_index = classes.index(1)
        else:
            positive_class_index = len(classes) - 1

    model = loaded_model
    scaler = loaded_scaler
    return model, scaler


def preprocess_vitals(vitals: dict) -> pd.DataFrame:
    """Apply the same zero-to-median imputation used during model training."""
    row = {
        "Pregnancies": vitals["pregnancies"],
        "Glucose": vitals["glucose"],
        "BloodPressure": vitals["blood_pressure"],
        "SkinThickness": vitals["skin_thickness"],
        "Insulin": vitals["insulin"],
        "BMI": vitals["bmi"],
        "DiabetesPedigreeFunction": vitals["pedigree_function"],
        "Age": vitals["age"],
    }

    for field in DEFAULT_MEDIANS:
        if row[field] == 0:
            row[field] = feature_medians[field]

    return pd.DataFrame([row], columns=FEATURE_COLUMNS)


def fallback_risk_score(vitals: dict) -> Tuple[float, int]:
    glucose = vitals["glucose"] if vitals["glucose"] > 0 else feature_medians["Glucose"]
    bmi = vitals["bmi"] if vitals["bmi"] > 0 else feature_medians["BMI"]
    age = vitals["age"]
    pedigree = vitals["pedigree_function"]

    score = (
        (glucose / 200.0) * 0.35
        + (bmi / 40.0) * 0.25
        + (age / 80.0) * 0.20
        + (pedigree / 2.5) * 0.10
        + (vitals["blood_pressure"] / 120.0) * 0.10
    )
    prob = float(min(max(score, 0.05), 0.95))
    outcome = 1 if prob >= 0.5 else 0
    return prob, outcome


def predict_diabetes_risk(vitals: dict) -> Tuple[float, int]:
    """
    Returns (probability_of_diabetes, outcome_class).
    outcome_class: 1 = high risk, 0 = low risk
    """
    if model is None or scaler is None:
        return fallback_risk_score(vitals)

    try:
        features_df = preprocess_vitals(vitals)
        features_scaled = scaler.transform(features_df)
        proba = model.predict_proba(features_scaled)[0]
        prob = float(proba[positive_class_index])
        outcome = 1 if prob >= 0.5 else 0
        return prob, outcome
    except Exception as exc:
        print(f"ML prediction failed, using fallback scoring: {exc}")
        return fallback_risk_score(vitals)
