Write-Host "🔧 Fixing Python Imports" -ForegroundColor Green
Write-Host "=" * 50

# Fix auth.py
$authSchema = @"
from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "user"

class RefreshTokenRequest(BaseModel):
    refresh_token: str
"@

$authSchema | Out-File -FilePath "app\schemas\auth.py" -Encoding UTF8 -Force
Write-Host "✅ Fixed app/schemas/auth.py" -ForegroundColor Green

# Fix user.py
$userSchema = @"
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    VENDOR = "vendor"
    ADMIN = "admin"
    USER = "user"

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole = UserRole.USER
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True
"@

$userSchema | Out-File -FilePath "app\schemas\user.py" -Encoding UTF8 -Force
Write-Host "✅ Fixed app/schemas/user.py" -ForegroundColor Green

# Fix vendor.py
$vendorSchema = @"
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class VendorStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class VendorBase(BaseModel):
    business_name: str
    business_type: str
    contact_person: str
    phone_number: str
    address: str
    tax_id: Optional[str] = None
    business_registration_number: Optional[str] = None

class VendorCreate(VendorBase):
    user_id: str

class VendorUpdate(BaseModel):
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    contact_person: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    business_registration_number: Optional[str] = None
    status: Optional[VendorStatus] = None

class VendorInDB(VendorBase):
    id: str
    user_id: str
    status: VendorStatus = VendorStatus.PENDING
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VendorResponse(VendorBase):
    id: str
    user_id: str
    status: VendorStatus
    created_at: datetime
    user: Optional[dict] = None
"@

$vendorSchema | Out-File -FilePath "app\schemas\vendor.py" -Encoding UTF8 -Force
Write-Host "✅ Fixed app/schemas/vendor.py" -ForegroundColor Green

# Fix auth_service.py
$authService = @"
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.database.supabase_client import SupabaseManager
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.user import UserCreate, UserRole
from app.utils.security import (
    verify_password, 
    get_password_hash, 
    create_tokens,
    verify_token
)
import logging

logger = logging.getLogger(__name__)

class AuthService:
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        \"\"\"Authenticate user with email and password\"\"\"
        try:
            # First, try to get user by email from Supabase
            result = await SupabaseManager.execute_query(
                table="users",
                operation="select",
                filters={"email": email},
                single=True
            )
            
            if not result["success"] or not result["data"]:
                return None
            
            user = result["data"]
            
            # Verify password (assuming password_hash field in your users table)
            if not verify_password(password, user.get("password_hash", "")):
                return None
            
            # Check if user is active
            if not user.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User account is inactive"
                )
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    @staticmethod
    async def register_user(user_data: RegisterRequest) -> Dict[str, Any]:
        \"\"\"Register a new user\"\"\"
        try:
            # Check if user already exists
            existing_user = await SupabaseManager.execute_query(
                table="users",
                operation="select",
                filters={"email": user_data.email}
            )
            
            if existing_user["success"] and existing_user["data"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash password
            hashed_password = get_password_hash(user_data.password)
            
            # Prepare user data for Supabase
            supabase_user_data = {
                "email": user_data.email,
                "name": user_data.name,
                "role": user_data.role,
                "password_hash": hashed_password,
                "is_active": True
            }
            
            # Create user in Supabase
            result = await SupabaseManager.execute_query(
                table="users",
                operation="insert",
                data=supabase_user_data
            )
            
            if not result["success"]:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
            
            user = result["data"][0] if result["data"] else {}
            
            # Create vendor profile if role is vendor
            if user_data.role == UserRole.VENDOR:
                vendor_data = {
                    "user_id": user["id"],
                    "business_name": f"{user_data.name}'s Business",
                    "business_type": "general",
                    "contact_person": user_data.name,
                    "phone_number": "",
                    "address": "",
                    "status": "pending"
                }
                
                await SupabaseManager.execute_query(
                    table="vendors",
                    operation="insert",
                    data=vendor_data
                )
            
            # Generate tokens
            tokens = create_tokens(user["id"], user_data.role)
            
            return {
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "role": user["role"],
                    "is_active": user["is_active"]
                },
                **tokens
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    @staticmethod
    async def login_user(login_data: LoginRequest) -> Dict[str, Any]:
        \"\"\"Login user\"\"\"
        user = await AuthService.authenticate_user(login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate tokens
        tokens = create_tokens(user["id"], user.get("role", "user"))
        
        return {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
                "is_active": user["is_active"]
            },
            **tokens
        }
    
    @staticmethod
    async def get_current_user(token: str) -> Dict[str, Any]:
        \"\"\"Get current user from token\"\"\"
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from Supabase
        result = await SupabaseManager.execute_query(
            table="users",
            operation="select",
            filters={"id": user_id},
            single=True
        )
        
        if not result["success"] or not result["data"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return result["data"]
    
    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Dict[str, str]:
        \"\"\"Refresh access token using refresh token\"\"\"
        payload = verify_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("sub")
        role = payload.get("role", "user")
        
        # Create new access token
        token_data = {"sub": user_id, "role": role}
        access_token = create_tokens(user_id, role)["access_token"]
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
"@

$authService | Out-File -FilePath "app\services\auth_service.py" -Encoding UTF8 -Force
Write-Host "✅ Fixed app/services/auth_service.py" -ForegroundColor Green

# Fix security.py
$security = @"
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    \"\"\"Verify a password against its hash\"\"\"
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    \"\"\"Hash a password\"\"\"
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    \"\"\"Create JWT access token\"\"\"
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    \"\"\"Create JWT refresh token\"\"\"
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    \"\"\"Verify JWT token\"\"\"
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Token verification failed: {e}")
        return None

def create_tokens(user_id: str, role: str) -> Dict[str, str]:
    \"\"\"Create both access and refresh tokens\"\"\"
    token_data = {"sub": user_id, "role": role}
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
"@

$security | Out-File -FilePath "app\utils\security.py" -Encoding UTF8 -Force
Write-Host "✅ Fixed app/utils/security.py" -ForegroundColor Green

Write-Host "`n✅ All files fixed!" -ForegroundColor Green
Write-Host "Try running again: python -m uvicorn app.main:app --reload --port 8000" -ForegroundColor Yellow.\fix_imports.ps1