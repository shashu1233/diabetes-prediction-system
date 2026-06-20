import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)  # "admin" or "user"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)  # "male", "female", "other"
    height = Column(Float, nullable=True)  # in cm
    weight = Column(Float, nullable=True)  # in kg
    phone = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="profile")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pregnancies = Column(Integer, nullable=False)
    glucose = Column(Integer, nullable=False)
    blood_pressure = Column(Integer, nullable=False)
    skin_thickness = Column(Integer, nullable=False)
    insulin = Column(Integer, nullable=False)
    bmi = Column(Float, nullable=False)
    pedigree_function = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    result_probability = Column(Float, nullable=False)
    result_class = Column(Integer, nullable=False)  # 0 or 1
    gemini_suggestion = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="predictions")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="feedbacks")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(String, nullable=False)  # "email", "sms", "whatsapp"
    content = Column(String, nullable=False)
    status = Column(String, default="sent", nullable=False)  # "sent", "failed"
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")
