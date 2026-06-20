import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# User Profile schemas
class ProfileUpdate(BaseModel):
    full_name: str
    age: int = Field(..., ge=0, le=120)
    gender: str = Field(..., description="male, female, or other")
    height: Optional[float] = Field(None, ge=30, le=300)
    weight: Optional[float] = Field(None, ge=10, le=500)
    phone: Optional[str] = None

class ProfileOut(BaseModel):
    full_name: str
    age: int
    gender: str
    height: Optional[float] = None
    weight: Optional[float] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True

# User schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[str] = "user"  # Default to "user", but allow creating admin if specified

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime.datetime
    profile: Optional[ProfileOut] = None

    class Config:
        from_attributes = True

# Prediction schemas
class PredictionInput(BaseModel):
    pregnancies: int = Field(0, ge=0, le=20)
    glucose: int = Field(..., ge=0, le=300)
    blood_pressure: int = Field(..., ge=0, le=200)
    skin_thickness: int = Field(0, ge=0, le=100)
    insulin: int = Field(0, ge=0, le=1000)
    bmi: float = Field(..., ge=0.0, le=100.0)
    pedigree_function: float = Field(..., ge=0.0, le=5.0)
    age: int = Field(..., ge=0, le=120)

class PredictionOut(BaseModel):
    id: int
    pregnancies: int
    glucose: int
    blood_pressure: int
    skin_thickness: int
    insulin: int
    bmi: float
    pedigree_function: float
    age: int
    result_probability: float
    result_class: int
    gemini_suggestion: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Feedback schemas
class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class FeedbackOut(BaseModel):
    id: int
    user_id: int
    username: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Notification schemas
class NotificationOut(BaseModel):
    id: int
    user_id: int
    notification_type: str
    content: str
    status: str
    sent_at: datetime.datetime

    class Config:
        from_attributes = True
