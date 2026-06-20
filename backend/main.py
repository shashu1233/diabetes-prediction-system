import os
import datetime
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

# Database imports
from backend.database import get_db, engine, Base
import backend.models as models
import backend.schemas as schemas
import backend.auth as auth
from backend.gemini_service import generate_gemini_suggestion
from backend.notification_service import send_notification
from backend.ml_inference import load_models, predict_diabetes_risk

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Diabetes Prediction System API",
    description="Backend API for User Auth, ML Predictions, Gemini Wellness advice, and Analytics.",
    version="1.0.0"
)

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load ML model and scaler (auto-trains on first run if artifacts are missing)
load_models()


# --- AUTH ENDPOINTS ---

@app.post("/api/auth/register", response_model=schemas.UserOut)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing_user = db.query(models.User).filter(
        (models.User.username == user_data.username) | (models.User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Auto-assign admin role if username contains "admin" (for developer testing convenience)
    role = user_data.role
    if "admin" in user_data.username.lower():
        role = "admin"

    # Create new user
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        password_hash=auth.hash_password(user_data.password),
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Initialize empty profile
    db_profile = models.UserProfile(
        user_id=db_user.id,
        full_name=db_user.username,
        age=30,
        gender="other"
    )
    db.add(db_profile)
    db.commit()

    # Re-fetch user with profile loaded
    db.refresh(db_user)
    
    # Trigger notification
    send_notification(
        db, 
        db_user.id, 
        "email", 
        f"Welcome to Diabetes Prediction System, {db_user.username}! Your account has been registered successfully."
    )
    
    return db_user


@app.post("/api/auth/login", response_model=schemas.Token)
def login_user(login_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Find user by username (or email)
    user = db.query(models.User).filter(
        (models.User.username == login_data.username) | (models.User.email == login_data.username)
    ).first()
    
    if not user or not auth.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# --- PROFILE ENDPOINTS ---

@app.get("/api/profile", response_model=schemas.ProfileOut)
def get_profile(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.put("/api/profile", response_model=schemas.ProfileOut)
def update_profile(
    profile_data: schemas.ProfileUpdate, 
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(get_db)
):
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.UserProfile(user_id=current_user.id)
        db.add(profile)

    profile.full_name = profile_data.full_name
    profile.age = profile_data.age
    profile.gender = profile_data.gender
    profile.height = profile_data.height
    profile.weight = profile_data.weight
    profile.phone = profile_data.phone

    db.commit()
    db.refresh(profile)
    return profile


# --- PREDICTION ENDPOINTS ---

@app.post("/api/predictions/predict", response_model=schemas.PredictionOut)
async def predict_risk(
    vitals: schemas.PredictionInput, 
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(get_db)
):
    vitals_dict = vitals.model_dump()
    prob, outcome = predict_diabetes_risk(vitals_dict)

    # Call Gemini (asynchronous call) for wellness advice
    gemini_text = await generate_gemini_suggestion(
        vitals.pregnancies,
        vitals.glucose,
        vitals.blood_pressure,
        vitals.skin_thickness,
        vitals.insulin,
        vitals.bmi,
        vitals.pedigree_function,
        vitals.age,
        prob,
        outcome
    )

    # Save to database
    db_pred = models.Prediction(
        user_id=current_user.id,
        pregnancies=vitals.pregnancies,
        glucose=vitals.glucose,
        blood_pressure=vitals.blood_pressure,
        skin_thickness=vitals.skin_thickness,
        insulin=vitals.insulin,
        bmi=vitals.bmi,
        pedigree_function=vitals.pedigree_function,
        age=vitals.age,
        result_probability=prob,
        result_class=outcome,
        gemini_suggestion=gemini_text
    )
    db.add(db_pred)
    db.commit()
    db.refresh(db_pred)

    # Send dynamic Email/SMS alert based on outcome
    alert_subject = "⚠️ Alert: High Risk Diabetes Assessment" if outcome == 1 else "✅ Report: Healthy Diabetes Assessment"
    alert_content = f"Hello {current_user.username}. Your recent diabetes risk score is {(prob*100):.1f}%. Result: {'High Risk' if outcome == 1 else 'Low Risk'}. Log in to view recommendations."
    
    send_notification(db, current_user.id, "email", f"{alert_subject} - {alert_content}")
    if outcome == 1:
        # Send SMS/WhatsApp warning for high risk
        send_notification(db, current_user.id, "sms", f"Alert: High diabetes risk detected ({prob*100:.1f}%). Please consult your doctor.")
        send_notification(db, current_user.id, "whatsapp", f"Hello! Your diabetes health assessment indicates an elevated risk level. Review details in your dashboard.")

    return db_pred


@app.get("/api/predictions/history", response_model=List[schemas.PredictionOut])
def get_prediction_history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    glucose_min: Optional[int] = None,
    glucose_max: Optional[int] = None,
    bmi_min: Optional[float] = None,
    bmi_max: Optional[float] = None,
    outcome: Optional[int] = None
):
    query = db.query(models.Prediction)
    
    # Non-admins only see their own predictions
    if current_user.role != "admin":
        query = query.filter(models.Prediction.user_id == current_user.id)
    
    # Filter operations
    if glucose_min is not None:
        query = query.filter(models.Prediction.glucose >= glucose_min)
    if glucose_max is not None:
        query = query.filter(models.Prediction.glucose <= glucose_max)
    if bmi_min is not None:
        query = query.filter(models.Prediction.bmi >= bmi_min)
    if bmi_max is not None:
        query = query.filter(models.Prediction.bmi <= bmi_max)
    if outcome is not None:
        query = query.filter(models.Prediction.result_class == outcome)
        
    return query.order_by(models.Prediction.created_at.desc()).all()


# --- FEEDBACK ENDPOINTS ---

@app.post("/api/feedbacks", response_model=schemas.FeedbackOut)
def create_feedback(
    feedback: schemas.FeedbackCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db_feedback = models.Feedback(
        user_id=current_user.id,
        rating=feedback.rating,
        comment=feedback.comment
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    # Add username to response serialization dynamically
    res = schemas.FeedbackOut(
        id=db_feedback.id,
        user_id=db_feedback.user_id,
        username=current_user.username,
        rating=db_feedback.rating,
        comment=db_feedback.comment,
        created_at=db_feedback.created_at
    )
    return res


@app.get("/api/feedbacks", response_model=List[schemas.FeedbackOut])
def get_all_feedbacks(
    admin_user: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db)
):
    results = db.query(models.Feedback, models.User.username).join(
        models.User, models.Feedback.user_id == models.User.id
    ).order_by(models.Feedback.created_at.desc()).all()
    
    feedbacks = []
    for f, username in results:
        feedbacks.append(
            schemas.FeedbackOut(
                id=f.id,
                user_id=f.user_id,
                username=username,
                rating=f.rating,
                comment=f.comment,
                created_at=f.created_at
            )
        )
    return feedbacks


# --- ADMIN CONTROL ENDPOINTS ---

@app.get("/api/admin/users", response_model=List[schemas.UserOut])
def get_all_users(
    admin_user: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db)
):
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@app.get("/api/admin/notifications", response_model=List[schemas.NotificationOut])
def get_all_notifications(
    admin_user: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db)
):
    return db.query(models.NotificationLog).order_by(models.NotificationLog.sent_at.desc()).all()


# --- DASHBOARD & ANALYTICS STATS (POWER BI DATA PROVIDER) ---

@app.get("/api/admin/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Compiles real-time user growth, prediction accuracy indicators,
    and visual distribution stats to feed interactive charts.
    """
    total_users = db.query(models.User).count()
    total_predictions = db.query(models.Prediction).count()
    
    # Calculate average risk probability
    avg_risk = db.query(func.avg(models.Prediction.result_probability)).scalar() or 0.0
    
    # Calculate Risk distribution (Low Risk = Outcome 0, High Risk = Outcome 1)
    high_risk_count = db.query(models.Prediction).filter(models.Prediction.result_class == 1).count()
    low_risk_count = db.query(models.Prediction).filter(models.Prediction.result_class == 0).count()
    
    # Average Vitals of predictions
    avg_glucose = db.query(func.avg(models.Prediction.glucose)).scalar() or 0.0
    avg_bmi = db.query(func.avg(models.Prediction.bmi)).scalar() or 0.0
    avg_age = db.query(func.avg(models.Prediction.age)).scalar() or 0.0

    # User growth (Signups per day for last 7 days)
    today = datetime.datetime.utcnow().date()
    user_growth = []
    prediction_growth = []
    
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        start_dt = datetime.datetime.combine(day, datetime.time.min)
        end_dt = datetime.datetime.combine(day, datetime.time.max)
        
        # User signups
        signups = db.query(models.User).filter(
            models.User.created_at >= start_dt,
            models.User.created_at <= end_dt
        ).count()
        
        # Predictions made
        preds = db.query(models.Prediction).filter(
            models.Prediction.created_at >= start_dt,
            models.Prediction.created_at <= end_dt
        ).count()
        
        user_growth.append({"date": day.strftime("%b %d"), "count": signups})
        prediction_growth.append({"date": day.strftime("%b %d"), "count": preds})

    # Feedback score
    avg_rating = db.query(func.avg(models.Feedback.rating)).scalar() or 0.0

    # Return structure
    return {
        "total_users": total_users,
        "total_predictions": total_predictions,
        "avg_risk_probability": round(float(avg_risk), 3),
        "avg_glucose": round(float(avg_glucose), 1),
        "avg_bmi": round(float(avg_bmi), 1),
        "avg_age": round(float(avg_age), 1),
        "avg_rating": round(float(avg_rating), 2),
        "risk_distribution": {
            "high_risk": high_risk_count,
            "low_risk": low_risk_count
        },
        "user_growth": user_growth,
        "prediction_growth": prediction_growth,
        "model_accuracy": 0.7338  # Pre-calculated classifier test accuracy
    }


# Serve Frontend Static Files
# We mount the "frontend" directory to serve static index.html, JS, and CSS files.
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return HTMLResponse(content="<h1>Welcome to Diabetes Prediction System</h1><p>Frontend static files not found.</p>", status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
