# main.py
from __future__ import annotations
import fastapi
from fastapi import FastAPI, HTTPException, UploadFile, Form, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client, Client
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Initialize FastAPI
app = FastAPI(title="Lanka Pass Travel API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencies
async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = auth_header.split(" ")[1]
    try:
        user_res = supabase.auth.get_user(token)
        if not user_res.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_data = supabase.table("users").select("*").eq("id", user_res.user.id).execute()
        if not user_data.data:
            return {
                "id": user_res.user.id,
                "email": user_res.user.email,
                "role": user_res.user.user_metadata.get("role", "user"),
                "name": user_res.user.user_metadata.get("name", "")
            }
        return user_data.data[0]
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# Auth API
@app.post("/api/auth/login")
async def login(request: Request):
    try:
        # Try both form and json for robustness
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()
            email = data.get("email") or data.get("username")
            password = data.get("password")
        else:
            form_data = await request.form()
            email = form_data.get("username") or form_data.get("email")
            password = form_data.get("password")
        
        if not email or not password:
             raise HTTPException(status_code=400, detail="Credentials required")

        auth_res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        user_id = auth_res.user.id
        user_data = supabase.table("users").select("*").eq("id", user_id).execute()
        
        user_profile = user_data.data[0] if user_data.data else {
            "id": user_id,
            "email": auth_res.user.email,
            "role": auth_res.user.user_metadata.get("role", "user"),
            "name": auth_res.user.user_metadata.get("name", ""),
            "is_active": True
        }
        
        return {
            "access_token": auth_res.session.access_token,
            "token_type": "bearer",
            "user": user_profile
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")

@app.post("/api/auth/register")
async def register(request: Request):
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        name = data.get("name")
        role = data.get("role", "user")
        
        # Create auth user
        auth_res = supabase.auth.admin.create_user({
            "email": str(email),
            "password": password,
            "email_confirm": True,
            "user_metadata": {"role": role, "name": name}
        })
        user_id = auth_res.user.id
        
        # Create public user
        user_profile = {
            "id": user_id,
            "email": str(email),
            "name": name,
            "role": role,
            "is_active": True
        }
        supabase.table("users").insert(user_profile).execute()
        
        # Sign in
        login_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        return {
            "access_token": login_res.session.access_token,
            "token_type": "bearer",
            "user": user_profile
        }
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

# Admin API
@app.get("/api/admin/dashboard", dependencies=[Depends(require_admin)])
async def get_admin_dashboard():
    try:
        vendors = supabase.table("vendors").select("status").execute()
        users = supabase.table("users").select("role").execute()
        return {
            "stats": {
                "total_vendors": len(vendors.data or []),
                "pending": len([v for v in (vendors.data or []) if v["status"] == "pending"]),
                "approved": len([v for v in (vendors.data or []) if v["status"] == "approved"]),
                "rejected": len([v for v in (vendors.data or []) if v["status"] == "rejected"]),
                "total_users": len(users.data or [])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/vendors", dependencies=[Depends(require_admin)])
async def get_all_vendors():
    try:
        vendors = supabase.table("vendors").select("*").execute()
        return {"success": True, "vendors": vendors.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/vendors/{vendor_id}", dependencies=[Depends(require_admin)])
async def get_vendor_detail(vendor_id: str):
    try:
        vendor_res = supabase.table("vendors").select("*").eq("id", vendor_id).single().execute()
        services_res = supabase.table("vendor_services").select("*").eq("vendor_id", vendor_id).execute()
        return {
            "success": True,
            "vendor": vendor_res.data,
            "services": services_res.data or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/admin/vendors/{vendor_id}", dependencies=[Depends(require_admin)])
async def update_vendor_status(vendor_id: str, request: Request):
    data = await request.json()
    res = supabase.table("vendors").update({
        "status": data.get("status"),
        "status_reason": data.get("status_reason")
    }).eq("id", vendor_id).execute()
    return {"success": True, "vendor": res.data[0]}

# Vendor API
@app.post("/api/vendor/register", status_code=201)
async def register_vendor(request: Request):
    try:
        data = await request.json()
        
        # 1. Auth User
        auth_res = supabase.auth.admin.create_user({
            "email": data.get("email"),
            "password": data.get("password"),
            "email_confirm": True,
            "user_metadata": {"role": "vendor", "name": data.get("contactPerson")}
        })
        user_id = auth_res.user.id
        
        # 2. Public User
        supabase.table("users").insert({
            "id": user_id,
            "email": data.get("email"),
            "name": data.get("contactPerson"),
            "role": "vendor"
        }).execute()
        
        # 3. Vendor Profile
        db_vendor = {
            "user_id": user_id,
            "vendor_type": data.get("vendorType"),
            "business_name": data.get("businessName"),
            "contact_person": data.get("contactPerson"),
            "email": data.get("email"),
            "phone_number": data.get("phoneNumber"),
            "operating_areas": data.get("operatingAreas"),
            "business_address": data.get("businessAddress"),
            "bank_name": data.get("bankName"),
            "account_holder_name": data.get("accountHolderName"),
            "account_number": data.get("accountNumber"),
            "bank_branch": data.get("bankBranch"),
            "status": "pending"
        }
        res = supabase.table("vendors").insert(db_vendor).execute()
        vendor_id = res.data[0]["id"]
        
        # 4. Services
        services = data.get("services", [])
        for s in services:
            db_service = {
                "vendor_id": vendor_id,
                "service_name": s.get("serviceName"),
                "service_category": s.get("serviceCategory"),
                "retail_price": s.get("retailPrice")
            }
            supabase.table("vendor_services").insert(db_service).execute()
            
        return {"success": True, "vendor_id": vendor_id}
    except Exception as e:
        logger.error(f"Vendor reg error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vendor/profile")
async def get_vendor_profile(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "vendor":
        raise HTTPException(status_code=403, detail="Vendor access required")
    
    try:
        vendor_res = supabase.table("vendors").select("*").eq("user_id", current_user["id"]).single().execute()
        if not vendor_res.data:
             raise HTTPException(status_code=404, detail="Vendor profile not found")
        
        vendor_id = vendor_res.data["id"]
        services_res = supabase.table("vendor_services").select("*").eq("vendor_id", vendor_id).execute()
        
        return {
            "success": True,
            "vendor": vendor_res.data,
            "services": services_res.data or []
        }
    except Exception as e:
        logger.error(f"Profile fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vendor/stats")
async def get_vendor_stats(current_user: dict = Depends(get_current_user)):
    # Mock stats for now, can be expanded with real booking data later
    return {
        "success": True,
        "stats": {
            "total_bookings": 0,
            "pending_bookings": 0,
            "total_earnings": 0,
            "active_services": 0
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
