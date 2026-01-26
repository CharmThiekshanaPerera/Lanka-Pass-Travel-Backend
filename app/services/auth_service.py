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
        """Authenticate user with email and password"""
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
        """Register a new user"""
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
        """Login user"""
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
        """Get current user from token"""
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
        """Refresh access token using refresh token"""
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