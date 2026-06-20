import os
import hashlib
import secrets
import datetime
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkeyfor_diabetes_prediction_system_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# --- Secure Pure-Python Password Hashing using PBKDF2 ---
def hash_password(password: str) -> str:
    """Hash password using PBKDF2 with SHA-256."""
    salt = secrets.token_hex(16)
    iterations = 100000
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", 
        password.encode("utf-8"), 
        salt.encode("utf-8"), 
        iterations
    )
    hash_hex = hash_bytes.hex()
    return f"pbkdf2_sha256${iterations}${salt}${hash_hex}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored PBKDF2 hash."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = parts[2]
        stored_hash = parts[3]
        
        calculated_bytes = hashlib.pbkdf2_hmac(
            "sha256", 
            plain_password.encode("utf-8"), 
            salt.encode("utf-8"), 
            iterations
        )
        return calculated_bytes.hex() == stored_hash
    except Exception:
        return False

# --- JWT Token Generation & Validation ---
def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have administrative privileges."
        )
    return current_user
