from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import hashlib
import secrets
import json
import os

# Create router object
router = APIRouter()

# Pydantic models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "user"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# File-based storage (for testing)
USERS_FILE = "users.json"

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return []

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

@router.post("/register")
async def register(user_data: RegisterRequest):
    """Register a new user"""
    users = load_users()
    
    # Check if user already exists
    for user in users:
        if user["email"] == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create user
    user = {
        "id": str(len(users) + 1),
        "email": user_data.email,
        "name": user_data.name,
        "role": user_data.role,
        "password_hash": hashlib.sha256(user_data.password.encode()).hexdigest(),
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    users.append(user)
    save_users(users)
    
    # Generate token
    token = secrets.token_urlsafe(32)
    
    return TokenResponse(
        access_token=token,
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "is_active": user["is_active"]
        }
    )

@router.post("/login")
async def login(login_data: LoginRequest):
    """Login user"""
    users = load_users()
    
    # Find user
    user = None
    for u in users:
        if u["email"] == login_data.email:
            user = u
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check password
    password_hash = hashlib.sha256(login_data.password.encode()).hexdigest()
    if user["password_hash"] != password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Generate token
    token = secrets.token_urlsafe(32)
    
    return TokenResponse(
        access_token=token,
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "is_active": user["is_active"]
        }
    )

@router.get("/me")
async def get_current_user():
    """Get current user (mock)"""
    return {
        "user": {
            "id": "1",
            "email": "test@example.com",
            "name": "Test User",
            "role": "user",
            "is_active": True
        }
    }

@router.get("/test")
async def test_auth():
    """Test endpoint"""
    return {"message": "Auth module is working"}
