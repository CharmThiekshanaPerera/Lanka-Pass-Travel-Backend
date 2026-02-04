# main.py
from __future__ import annotations
import fastapi
from fastapi import FastAPI, HTTPException, UploadFile, Form, File, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import os
import io
import csv
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client, Client
import logging
from app.services.sms_service import SmsService
from app.services.chat_service import chat_service
from app.database.mongo_config import ensure_indexes, close_mongo_connection


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL", "").strip()
supabase_key = os.getenv("SUPABASE_KEY", "").strip()
if not supabase_url or not supabase_key:
    logger.error("CRITICAL: SUPABASE_URL or SUPABASE_KEY not set!")

supabase: Client = create_client(supabase_url, supabase_key)
# DEDICATED ADMIN CLIENT to avoid session pollution from auth.sign_in calls
supabase_admin: Client = create_client(supabase_url, supabase_key)

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

# MongoDB startup/shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize MongoDB indexes on startup"""
    # Run in background to avoid blocking app startup if connection is slow
    import asyncio
    asyncio.create_task(ensure_indexes())
    logger.info("MongoDB index creation started in background")

@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown"""
    await close_mongo_connection()
    logger.info("MongoDB connection closed on shutdown")

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
        
        user_id = user_res.user.id
        user_email = user_res.user.email
        user_role = user_res.user.user_metadata.get("role", "user") if user_res.user.user_metadata else "user"
        user_name = user_res.user.user_metadata.get("name", "") if user_res.user.user_metadata else ""

        try:
            user_data = supabase.table("users").select("*").eq("id", user_id).execute()
            if user_data.data:
                return user_data.data[0]
        except Exception:
            pass

        return {
            "id": user_id,
            "email": user_email,
            "role": user_role,
            "name": user_name
        }
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_vendor(user: dict = Depends(get_current_user)):
    if user.get("role") != "vendor":
        raise HTTPException(status_code=403, detail="Vendor access required")
    return user

async def upload_file_to_storage(file: UploadFile, vendor_id: str, file_type: str, service_id: Optional[str] = None):
    """Upload file to Supabase Storage"""
    try:
        # Read file content
        content = await file.read()
        
        # Generate unique filename
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        
        # Determine file path
        if service_id:
            file_path = f"vendors/{vendor_id}/services/{service_id}/{unique_filename}"
        else:
            file_path = f"vendors/{vendor_id}/{file_type}/{unique_filename}"
        
        # Upload to storage
        result = supabase_admin.storage.from_("vendor-files").upload(
            file_path,
            content,
            {"content-type": file.content_type}
        )
        
        # Get public URL
        public_url = supabase_admin.storage.from_("vendor-files").get_public_url(file_path)
        
        return public_url
        
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise e

async def require_staff(user: dict = Depends(get_current_user)):
    """Allow both admin and manager roles"""
    if user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Staff access required")
    return user


# pydantic models
class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[EmailStr] = None
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "user"

class CommissionUpdateRequest(BaseModel):
    commission_percent: float

class ManagerCreateRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class SendOtpRequest(BaseModel):
    phoneNumber: str

class VerifyOtpRequest(BaseModel):
    phoneNumber: str
    otpCode: str

class VendorStatusRequest(BaseModel):
    status: str
    status_reason: Optional[str] = None

class DeleteFileSchema(BaseModel):
    vendor_id: str
    file_url: str
    file_type: str
    service_id: Optional[str] = None

class ServiceSchema(BaseModel):
    serviceName: str
    serviceCategory: str
    serviceCategoryOther: Optional[str] = None
    serviceDescription: Optional[str] = None
    description: Optional[str] = None
    shortDescription: Optional[str] = None
    whatsIncluded: Optional[str] = None
    whatsNotIncluded: Optional[str] = None
    durationValue: Optional[int] = None
    durationUnit: Optional[str] = None
    languagesOffered: Optional[List[str]] = []
    languagesOther: Optional[str] = None
    groupSizeMin: Optional[int] = None
    groupSizeMax: Optional[int] = None
    dailyCapacity: Optional[int] = None
    operatingDays: Optional[List[str]] = []
    locationsCovered: Optional[List[str]] = []
    currency: str = "USD"
    retailPrice: float
    # New fields
    operatingHoursFrom: Optional[str] = None
    operatingHoursFromPeriod: Optional[str] = "AM"
    operatingHoursTo: Optional[str] = None
    operatingHoursToPeriod: Optional[str] = "PM"
    blackoutDates: Optional[List[str]] = []
    blackoutHolidays: Optional[bool] = False
    blackoutWeekends: Optional[bool] = False
    advanceBooking: Optional[str] = None
    advanceBookingOther: Optional[str] = None
    notSuitableFor: Optional[str] = None
    importantInfo: Optional[str] = None
    cancellationPolicy: Optional[str] = None
    accessibilityInfo: Optional[str] = None
    imageUrls: Optional[List[str]] = []
    serviceTimeSlots: Optional[List[Dict[str, Any]]] = []
    status: Optional[str] = "active"

class VendorRegisterRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = "123456"
    contactPerson: str
    vendorType: Optional[str] = None
    vendorTypeOther: Optional[str] = None
    businessName: str
    legalName: Optional[str] = None
    phoneNumber: Optional[str] = None
    phoneVerified: Optional[bool] = False
    operatingAreas: Optional[List[str]] = []
    operatingAreas_other: Optional[str] = None
    businessRegNumber: Optional[str] = None
    businessAddress: str
    taxId: Optional[str] = None
    bankName: Optional[str] = None
    bankNameOther: Optional[str] = None
    accountHolderName: Optional[str] = None
    accountNumber: Optional[str] = None
    bankBranch: Optional[str] = None
    # File URLs
    regCertificateUrl: Optional[str] = None
    nicPassportUrl: Optional[str] = None
    tourismLicenseUrl: Optional[str] = None
    logoUrl: Optional[str] = None
    coverImageUrl: Optional[str] = None
    galleryUrls: Optional[List[str]] = []
    # Agreements
    acceptTerms: bool = False
    acceptCommission: bool = False
    acceptCancellation: bool = False
    grantRights: bool = False
    confirmAccuracy: bool = False
    # Payout prefs
    # Services
    services: List[ServiceSchema] = []

class VendorUpdateSchema(BaseModel):
    businessName: Optional[str] = None
    legalName: Optional[str] = None
    contactPerson: Optional[str] = None
    phoneNumber: Optional[str] = None
    operatingAreas: Optional[List[str]] = None
    operatingAreasOther: Optional[str] = None
    vendorType: Optional[str] = None
    vendorTypeOther: Optional[str] = None
    businessAddress: Optional[str] = None
    businessRegNumber: Optional[str] = None
    taxId: Optional[str] = None
    bankName: Optional[str] = None
    bankNameOther: Optional[str] = None
    accountHolderName: Optional[str] = None
    accountNumber: Optional[str] = None
    bankBranch: Optional[str] = None
    bankBranch: Optional[str] = None
    regCertificateUrl: Optional[str] = None
    nicPassportUrl: Optional[str] = None
    tourismLicenseUrl: Optional[str] = None

# Chat and Update Request Models
class ChatMessageSchema(BaseModel):
    message: str
    attachments: Optional[List[Dict[str, Any]]] = []

class UpdateRequestApprovalSchema(BaseModel):
    pass  # No body needed for approval

class UpdateRequestRejectionSchema(BaseModel):
    reason: str


@app.post("/api/auth/send-otp")
async def send_otp(data: SendOtpRequest):
    try:
        success = await SmsService.send_otp(data.phoneNumber)
        if success:
            return {"success": True, "message": "OTP sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send OTP")
    except Exception as e:
        logger.error(f"Send OTP error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/verify-otp")
async def verify_otp(data: VerifyOtpRequest):
    try:
        is_valid = await SmsService.verify_otp(data.phoneNumber, data.otpCode)
        if is_valid:
            return {"success": True, "message": "OTP verified successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    except Exception as e:
        logger.error(f"Verify OTP error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Auth API
@app.post("/api/auth/login")
async def login(data: LoginRequest):
    try:
        email = data.email or data.username
        if not email or not data.password:
             raise HTTPException(status_code=400, detail="Credentials required")

        auth_res = supabase.auth.sign_in_with_password({
            "email": str(email),
            "password": data.password
        })
        
        user_id = auth_res.user.id
        user_email = auth_res.user.email
        user_role = auth_res.user.user_metadata.get("role", "user") if auth_res.user.user_metadata else "user"
        user_name = auth_res.user.user_metadata.get("name", "") if auth_res.user.user_metadata else ""

        try:
            user_data = supabase.table("users").select("*").eq("id", user_id).execute()
            user_profile = user_data.data[0] if user_data.data else {
                "id": user_id,
                "email": user_email,
                "role": user_role,
                "name": user_name,
                "is_active": True
            }
        except Exception as query_err:
            logger.warning(f"Could not fetch extended user profile: {str(query_err)}")
            user_profile = {
                "id": user_id,
                "email": user_email,
                "role": user_role,
                "name": user_name,
                "is_active": True
            }
        
        return {
            "access_token": auth_res.session.access_token,
            "token_type": "bearer",
            "user": user_profile
        }
    except Exception as e:
        logger.exception("Login failed")
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")

@app.post("/api/auth/register")
async def register(data: RegisterRequest):
    try:
        role = data.role
        
        if role in ["user", "vendor"]:
            # Use the standard client for public registration
            auth_res = supabase.auth.sign_up({
                "email": str(data.email),
                "password": data.password,
                "options": {
                    "data": {"role": role, "name": data.name}
                }
            })
            user_id = auth_res.user.id
            
            user_profile = {
                "id": user_id,
                "email": str(data.email),
                "name": data.name,
                "role": role,
                "is_active": True
            }
            # Use admin client to insert to ensure no RLS issues during initial creation
            supabase_admin.table("users").insert(user_profile).execute()
            
            login_res = supabase.auth.sign_in_with_password({"email": str(data.email), "password": data.password})
            
            return {
                "access_token": login_res.session.access_token,
                "token_type": "bearer",
                "user": user_profile
            }
        else:
            # For staff roles, use admin client
            auth_res = supabase_admin.auth.admin.create_user({
                "email": str(data.email),
                "password": data.password,
                "email_confirm": True,
                "user_metadata": {"role": role, "name": data.name}
            })
            user_id = auth_res.user.id
            
            user_profile = {
                "id": user_id,
                "email": str(data.email),
                "name": data.name,
                "role": role,
                "is_active": True
            }
            supabase_admin.table("users").insert(user_profile).execute()
            
            # Use standard client for login
            login_res = supabase.auth.sign_in_with_password({"email": str(data.email), "password": data.password})
            
            return {
                "access_token": login_res.session.access_token,
                "token_type": "bearer",
                "user": user_profile
            }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Registration failed for email {data.email} with role {data.role}: {error_msg}")
        
        if "User not allowed" in error_msg:
             detail = f"Supabase Auth Error: 'User not allowed' for {data.email}. Please ensure your Service Role key is correct and 'Enable manual user confirmation' or other restrictions in Supabase are not blocking admin user creation."
        elif "already registered" in error_msg.lower() or "unique constraint" in error_msg.lower():
             detail = f"The email {data.email} is already registered."
        else:
             detail = f"Registration failed: {error_msg}"
             
        raise HTTPException(status_code=500, detail=detail)

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

# Admin API
@app.get("/api/admin/dashboard", dependencies=[Depends(require_staff)])
async def get_admin_dashboard():
    try:
        # Use ADMIN client to ensure we see all data regardless of RLS pollution
        vendors = supabase_admin.table("vendors").select("status").execute()
        users = supabase_admin.table("users").select("role").execute()
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

@app.get("/api/admin/vendors", dependencies=[Depends(require_staff)])
async def get_vendors_admin(status: Optional[str] = None):
    try:
        query = supabase_admin.table("vendors").select("*")
        if status:
            query = query.eq("status", status)
        res = query.order("created_at", desc=True).execute()
        return {"success": True, "vendors": res.data or []}
    except Exception as e:
        logger.error(f"Fetch vendors admin error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/vendors/{vendor_id}", dependencies=[Depends(require_staff)])
async def get_vendor_detail(vendor_id: str):
    try:
        vendor_res = supabase_admin.table("vendors").select("*").eq("id", vendor_id).single().execute()
        services_res = supabase_admin.table("vendor_services").select("*").eq("vendor_id", vendor_id).execute()
        return {
            "success": True,
            "vendor": vendor_res.data,
            "services": services_res.data or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/admin/vendors/{vendor_id}", dependencies=[Depends(require_admin)])
async def update_vendor_status(vendor_id: str, data: VendorStatusRequest):
    res = supabase_admin.table("vendors").update({
        "status": data.status,
        "status_reason": data.status_reason
    }).eq("id", vendor_id).execute()
    return {"success": True, "vendor": res.data[0]}

@app.patch("/api/admin/services/{service_id}/commission", dependencies=[Depends(require_admin)])
async def update_service_commission(service_id: str, data: CommissionUpdateRequest):
    try:
        commission_percent = data.commission_percent
        
        if not (0 <= commission_percent <= 100):
             raise HTTPException(status_code=400, detail="Commission must be a percentage between 0 and 100")

        # Get current service details
        service_res = supabase_admin.table("vendor_services").select("retail_price").eq("id", service_id).single().execute()
        if not service_res.data:
            raise HTTPException(status_code=404, detail="Service not found")
            
        retail_price = float(service_res.data["retail_price"] or 0)
        
        # Calculate
        commission_amount = retail_price * (commission_percent / 100.0)
        net_price = retail_price - commission_amount
        
        # Update
        update_data = {
            "commission": commission_amount,
            "net_price": net_price
        }
        
        res = supabase_admin.table("vendor_services").update(update_data).eq("id", service_id).execute()
        
        return {
            "success": True, 
            "service": res.data[0],
            "calculation": {
                "retail_price": retail_price,
                "commission_percent": commission_percent,
                "commission_amount": commission_amount,
                "net_price": net_price
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Commission update error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Manager Management (Admin Only)
@app.get("/api/admin/managers", dependencies=[Depends(require_admin)])
async def get_managers():
    try:
        users = supabase_admin.table("users").select("*").eq("role", "manager").execute()
        return {"success": True, "managers": users.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/managers", dependencies=[Depends(require_admin)])
async def create_manager(data: ManagerCreateRequest):
    try:
        # Create auth user using ADMIN client
        auth_res = supabase_admin.auth.admin.create_user({
            "email": str(data.email),
            "password": data.password,
            "email_confirm": True,
            "user_metadata": {"role": "manager", "name": data.name}
        })
        user_id = auth_res.user.id
        
        # Create public user
        user_profile = {
            "id": user_id,
            "email": str(data.email),
            "name": data.name,
            "role": "manager",
            "is_active": True
        }
        supabase_admin.table("users").insert(user_profile).execute()
        
        return {"success": True, "manager": user_profile}
    except Exception as e:
        logger.error(f"Create manager error: {str(e)}")
        error_msg = str(e)
        if "User already registered" in error_msg or "violates unique constraint" in error_msg:
             raise HTTPException(status_code=400, detail="This email is already registered.")
        if "Password should be at least" in error_msg:
             raise HTTPException(status_code=400, detail="Password is too weak. " + error_msg)
        raise HTTPException(status_code=500, detail=f"Failed to create manager: {error_msg}")

@app.delete("/api/admin/managers/{user_id}", dependencies=[Depends(require_admin)])
async def delete_manager(user_id: str):
    try:
        supabase_admin.auth.admin.delete_user(user_id)
        supabase_admin.table("users").delete().eq("id", user_id).execute()
        return {"success": True, "message": "Manager deleted"}
    except Exception as e:
        logger.error(f"Delete manager error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete manager: {str(e)}")

# Export Data (Staff Only)
@app.get("/api/admin/export/vendors", dependencies=[Depends(require_staff)])
async def export_vendors():
    try:
        vendors = supabase.table("vendors").select("*").execute()
        
        output = io.StringIO()
        fieldnames = [
            "id", "user_id", "business_name", "vendor_type", "status", 
            "contact_person", "email", "phone_number", "created_at"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for v in (vendors.data or []):
            row = {k: v.get(k, "") for k in fieldnames}
            writer.writerow(row)
            
        output.seek(0)
        
        return fastapi.Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=vendors_export_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))





# Vendor API
@app.post("/api/vendor/register", status_code=201)
async def register_vendor(data: VendorRegisterRequest):
    user_id = None
    vendor_id = None
    try:
        logger.info(f"Vendor registration: {data.email}")
        
        # 1. Auth User - Use ADMIN client
        # Default password to '123456' if not provided
        password = data.password if data.password else "123456"
        
        try:
            auth_res = supabase_admin.auth.admin.create_user({
                "email": str(data.email),
                "password": password,
                "email_confirm": True,
                "user_metadata": {"role": "vendor", "name": data.contactPerson}
            })
            user_id = auth_res.user.id
            logger.info(f"Auth user created: {user_id}")
        except Exception as e:
            logger.error(f"Auth creation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Auth creation failed: {str(e)}")
        
        # 2. Public User
        try:
            supabase_admin.table("users").insert({
                "id": user_id,
                "email": str(data.email),
                "name": data.contactPerson,
                "role": "vendor"
            }).execute()
            logger.info(f"User profile created: {user_id}")
        except Exception as e:
            logger.error(f"Profile creation failed: {str(e)}")
            # Rollback: Delete auth user
            try:
                supabase_admin.auth.admin.delete_user(user_id)
                logger.info(f"Rolled back auth user: {user_id}")
            except Exception as rollback_err:
                logger.error(f"Rollback failed for auth user: {rollback_err}")
            raise HTTPException(status_code=500, detail=f"User profile failed: {str(e)}")
        
        # 3. Vendor Profile
        try:
            db_vendor = {
                "user_id": user_id,
                "vendor_type": data.vendorType,
                "vendor_type_other": data.vendorTypeOther,
                "business_name": data.businessName,
                "legal_name": data.legalName,
                "contact_person": data.contactPerson,
                "email": str(data.email),
                "phone_number": data.phoneNumber,
                "phone_verified": data.phoneVerified,
                "operating_areas": data.operatingAreas,
                "operating_areas_other": data.operatingAreas_other,
                "business_reg_number": data.businessRegNumber,
                "business_address": data.businessAddress,
                "tax_id": data.taxId,
                "bank_name": data.bankName,
                "bank_name_other": data.bankNameOther,
                "account_holder_name": data.accountHolderName,
                "account_number": data.accountNumber,
                "bank_branch": data.bankBranch,
                # URLs
                "reg_certificate_url": data.regCertificateUrl,
                "nic_passport_url": data.nicPassportUrl,
                "tourism_license_url": data.tourismLicenseUrl,
                "logo_url": data.logoUrl,
                "cover_image_url": data.coverImageUrl,
                "gallery_urls": data.galleryUrls,
                # Payout
                # Payout
                # Agreements
                "accept_terms": data.acceptTerms,
                "accept_commission": data.acceptCommission,
                "accept_cancellation": data.acceptCancellation,
                "grant_rights": data.grantRights,
                "confirm_accuracy": data.confirmAccuracy,
                "status": "pending"
            }
            res = supabase_admin.table("vendors").insert(db_vendor).execute()
            vendor_id = res.data[0]["id"]
            logger.info(f"Vendor profile created: {vendor_id}")
        except Exception as e:
            logger.error(f"Vendor profile error: {str(e)}")
            # Rollback: Delete user and auth
            try:
                supabase_admin.table("users").delete().eq("id", user_id).execute()
                logger.info(f"Rolled back user profile: {user_id}")
            except Exception as rollback_err:
                logger.error(f"Rollback failed for user profile: {rollback_err}")
            try:
                supabase_admin.auth.admin.delete_user(user_id)
                logger.info(f"Rolled back auth user: {user_id}")
            except Exception as rollback_err:
                logger.error(f"Rollback failed for auth user: {rollback_err}")
            raise HTTPException(status_code=500, detail=f"Vendor profile failed: {str(e)}")
        
        # 4. Services
        for s in data.services:
            try:
                db_service = {
                    "vendor_id": vendor_id,
                    "service_name": s.serviceName,
                    "service_category": s.serviceCategory,
                    "service_category_other": s.serviceCategoryOther,
                    "service_description": s.serviceDescription or s.description,
                    "short_description": s.shortDescription,
                    "whats_included": s.whatsIncluded,
                    "whats_not_included": s.whatsNotIncluded,
                    "duration_value": s.durationValue,
                    "duration_unit": s.durationUnit,
                    "languages_offered": s.languagesOffered,
                    "languages_other": s.languagesOther,
                    "group_size_min": s.groupSizeMin,
                    "group_size_max": s.groupSizeMax,
                    "daily_capacity": s.dailyCapacity,
                    "operating_days": s.operatingDays,
                    "locations_covered": s.locationsCovered,
                    "currency": s.currency,
                    "retail_price": s.retailPrice,
                    "commission": 0,
                    "net_price": s.retailPrice,
                    # New fields
                    "operating_hours_from": s.operatingHoursFrom,
                    "operating_hours_from_period": s.operatingHoursFromPeriod,
                    "operating_hours_to": s.operatingHoursTo,
                    "operating_hours_to_period": s.operatingHoursToPeriod,
                    "blackout_dates": s.blackoutDates,
                    "blackout_holidays": s.blackoutHolidays,
                    "blackout_weekends": s.blackoutWeekends,
                    "advance_booking": s.advanceBooking,
                    "advance_booking_other": s.advanceBookingOther,
                    "not_suitable_for": s.notSuitableFor,
                    "important_info": s.importantInfo,
                    "cancellation_policy": s.cancellationPolicy,
                    "accessibility_info": s.accessibilityInfo,
                    "image_urls": s.imageUrls
                }
                supabase_admin.table("vendor_services").insert(db_service).execute()
                logger.info(f"Service created: {s.serviceName}")
            except Exception as se:
                logger.error(f"Service insert error for {s.serviceName}: {str(se)}")
                # Rollback: Delete vendor, user, and auth
                try:
                    supabase_admin.table("vendors").delete().eq("id", vendor_id).execute()
                    logger.info(f"Rolled back vendor profile: {vendor_id}")
                except Exception as rollback_err:
                    logger.error(f"Rollback failed for vendor: {rollback_err}")
                try:
                    supabase_admin.table("users").delete().eq("id", user_id).execute()
                    logger.info(f"Rolled back user profile: {user_id}")
                except Exception as rollback_err:
                    logger.error(f"Rollback failed for user: {rollback_err}")
                try:
                    supabase_admin.auth.admin.delete_user(user_id)
                    logger.info(f"Rolled back auth user: {user_id}")
                except Exception as rollback_err:
                    logger.error(f"Rollback failed for auth: {rollback_err}")
                raise HTTPException(status_code=500, detail=f"Service registration failed for {s.serviceName}: {str(se)}")
                
        logger.info(f"Vendor registration completed successfully: {vendor_id}")
        return {"success": True, "vendor_id": vendor_id}
    except HTTPException: raise
    except Exception as e:
        logger.exception("Vendor registration exception")
        # Final catch-all rollback if we have IDs
        if vendor_id:
            try:
                supabase_admin.table("vendors").delete().eq("id", vendor_id).execute()
                logger.info(f"Final rollback - vendor: {vendor_id}")
            except: pass
        if user_id:
            try:
                supabase_admin.table("users").delete().eq("id", user_id).execute()
                logger.info(f"Final rollback - user: {user_id}")
            except: pass
            try:
                supabase_admin.auth.admin.delete_user(user_id)
                logger.info(f"Final rollback - auth: {user_id}")
            except: pass
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vendor/profile")
async def get_vendor_profile(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "vendor":
        raise HTTPException(status_code=403, detail="Vendor access required")
    try:
        # Use ADMIN client to bypass RLS issues for the authorized user
        vendor_res = supabase_admin.table("vendors").select("*").eq("user_id", current_user["id"]).single().execute()
        if not vendor_res.data: raise HTTPException(status_code=404, detail="Vendor profile not found")
        v_id = vendor_res.data["id"]
        s_res = supabase_admin.table("vendor_services").select("*").eq("vendor_id", v_id).execute()
        return {"success": True, "vendor": vendor_res.data, "services": s_res.data or []}
    except Exception as e:
        logger.error(f"Get vendor profile error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vendor/stats")
async def get_vendor_stats(current_user: dict = Depends(get_current_user)):
    return {"success": True, "stats": {"total_bookings": 0, "pending_bookings": 0, "total_earnings": 0, "active_services": 0}}

@app.put("/api/vendor/profile")
async def update_vendor_profile(data: VendorUpdateSchema, current_user: dict = Depends(get_current_user)):
    """
    Update vendor profile - Creates an approval request instead of direct update.
    Non-media field updates require admin/manager approval via chat.
    """
    if current_user.get("role") != "vendor":
        raise HTTPException(status_code=403, detail="Vendor access required")
    
    try:
        # Get current vendor data
        vendor_res = supabase_admin.table("vendors").select("*").eq("user_id", current_user["id"]).single().execute()
        if not vendor_res.data:
            raise HTTPException(status_code=404, detail="Vendor profile not found")
        
        vendor_id = vendor_res.data["id"]
        current_vendor_data = vendor_res.data
        
        # Field mapping from pydantic to database
        field_map = {
            "businessName": "business_name",
            "legalName": "legal_name",
            "contactPerson": "contact_person",
            "phoneNumber": "phone_number",
            "operatingAreas": "operating_areas",
            "operatingAreasOther": "operating_areas_other",
            "vendorType": "vendor_type",
            "vendorTypeOther": "vendor_type_other",
            "businessAddress": "business_address",
            "businessRegNumber": "business_reg_number",
            "taxId": "tax_id",
            "bankName": "bank_name",
            "bankNameOther": "bank_name_other",
            "accountHolderName": "account_holder_name",
            "accountNumber": "account_number",
            "bankBranch": "bank_branch",
            "bankBranch": "bank_branch",
            "regCertificateUrl": "reg_certificate_url",
            "nicPassportUrl": "nic_passport_url",
            "tourismLicenseUrl": "tourism_license_url"
        }
        
        # Prepare update data (only changed fields)
        requested_data = {}
        current_data_snapshot = {}
        changed_fields = []
        
        for pydantic_field, db_field in field_map.items():
            val = getattr(data, pydantic_field)
            if val is not None:
                current_val = current_vendor_data.get(db_field)
                # Only include if actually different
                if val != current_val:
                    requested_data[db_field] = val
                    current_data_snapshot[db_field] = current_val
                    changed_fields.append(pydantic_field)
        
        if not requested_data:
            return {"success": True, "message": "No changes detected", "pending_approval": False}
        
        # Create update request in MongoDB (requires approval)
        update_request = await chat_service.create_update_request(
            vendor_id=vendor_id,
            requested_by=current_user["id"],
            requested_by_name=current_user.get("name", current_user.get("email", "Vendor")),
            current_data=current_data_snapshot,
            requested_data=requested_data,
            changed_fields=changed_fields
        )
        
        if update_request:
            return {
                "success": True,
                "message": "Your profile update request has been submitted for approval. You will be notified once it is reviewed.",
                "pending_approval": True,
                "request_id": update_request.get("id"),
                "changed_fields": changed_fields
            }
        else:
            # MongoDB not available - cannot create approval request
            logger.error("MongoDB not available - cannot create approval request")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Approval service temporarily unavailable. Please try again later."
            )
        
    except Exception as e:
        logger.error(f"Update vendor profile error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SERVICE MANAGEMENT ENDPOINTS ====================

@app.post("/api/vendor/services", status_code=201)
async def create_vendor_service(s: ServiceSchema, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "vendor":
        raise HTTPException(status_code=403, detail="Vendor access required")
    
    try:
        # Get vendor ID first
        vendor_res = supabase_admin.table("vendors").select("id").eq("user_id", current_user["id"]).single().execute()
        if not vendor_res.data:
            raise HTTPException(status_code=404, detail="Vendor profile not found")
        
        vendor_id = vendor_res.data["id"]
        
        db_service = {
            "vendor_id": vendor_id,
            "service_name": s.serviceName,
            "service_category": s.serviceCategory,
            "service_category_other": s.serviceCategoryOther,
            "service_description": s.serviceDescription or s.description,
            "short_description": s.shortDescription,
            "whats_included": s.whatsIncluded,
            "whats_not_included": s.whatsNotIncluded,
            "duration_value": s.durationValue,
            "duration_unit": s.durationUnit,
            "languages_offered": s.languagesOffered,
            "languages_other": s.languagesOther,
            "group_size_min": s.groupSizeMin,
            "group_size_max": s.groupSizeMax,
            "daily_capacity": s.dailyCapacity,
            "operating_days": s.operatingDays,
            "locations_covered": s.locationsCovered,
            "currency": s.currency,
            "retail_price": s.retailPrice,
            "commission": 0,
            "net_price": s.retailPrice,
            "operating_hours_from": s.operatingHoursFrom,
            "operating_hours_from_period": s.operatingHoursFromPeriod,
            "operating_hours_to": s.operatingHoursTo,
            "operating_hours_to_period": s.operatingHoursToPeriod,
            "blackout_dates": s.blackoutDates,
            "blackout_holidays": s.blackoutHolidays,
            "blackout_weekends": s.blackoutWeekends,
            "advance_booking": s.advanceBooking,
            "advance_booking_other": s.advanceBookingOther,
            "not_suitable_for": s.notSuitableFor,
            "important_info": s.importantInfo,
            "cancellation_policy": s.cancellationPolicy,
            "accessibility_info": s.accessibilityInfo,
            "image_urls": s.imageUrls or [],
            "service_time_slots": s.serviceTimeSlots or []
        }
        
        # Create an approval request instead of direct insertion
        from app.services.chat_service import chat_service
        request = await chat_service.create_service_addition_request(
            vendor_id=vendor_id,
            requested_by=current_user["id"],
            requested_by_name=current_user.get("name") or vendor_id,
            requested_data=db_service
        )
        
        if request:
            return {
                "success": True, 
                "message": "Your new service has been submitted for approval. You can view its status in the support chat.",
                "pending_approval": True,
                "request_id": request["id"]
            }
        else:
            # MongoDB not available - cannot create approval request
            logger.error("MongoDB not available - cannot create service addition approval request")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Approval service temporarily unavailable. Please try again later."
            )
        
    except Exception as e:
        logger.error(f"Create service error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/vendor/services/{service_id}")
async def update_vendor_service(service_id: str, s: ServiceSchema, current_user: dict = Depends(get_current_user)):
    """
    Update vendor service - Creates an approval request for non-media changes.
    Media field updates (imageUrls) apply directly without approval.
    """
    if current_user.get("role") != "vendor":
        raise HTTPException(status_code=403, detail="Vendor access required")
    
    try:
        # Verify ownership
        vendor_res = supabase_admin.table("vendors").select("id").eq("user_id", current_user["id"]).single().execute()
        if not vendor_res.data:
            raise HTTPException(status_code=404, detail="Vendor profile not found")
        
        vendor_id = vendor_res.data["id"]
        
        # Get current service data
        service_res = supabase_admin.table("vendor_services").select("*").eq("id", service_id).eq("vendor_id", vendor_id).single().execute()
        if not service_res.data:
            raise HTTPException(status_code=404, detail="Service not found or access denied")
        
        current_service_data = service_res.data
        
        # Field mapping from pydantic to database
        field_map = {
            "serviceName": "service_name",
            "serviceCategory": "service_category",
            "serviceCategoryOther": "service_category_other",
            "serviceDescription": "service_description",
            "shortDescription": "short_description",
            "whatsIncluded": "whats_included",
            "whatsNotIncluded": "whats_not_included",
            "durationValue": "duration_value",
            "durationUnit": "duration_unit",
            "languagesOffered": "languages_offered",
            "languagesOther": "languages_other",
            "groupSizeMin": "group_size_min",
            "groupSizeMax": "group_size_max",
            "dailyCapacity": "daily_capacity",
            "operatingDays": "operating_days",
            "locationsCovered": "locations_covered",
            "currency": "currency",
            "retailPrice": "retail_price",
            "operatingHoursFrom": "operating_hours_from",
            "operatingHoursFromPeriod": "operating_hours_from_period",
            "operatingHoursTo": "operating_hours_to",
            "operatingHoursToPeriod": "operating_hours_to_period",
            "blackoutDates": "blackout_dates",
            "blackoutHolidays": "blackout_holidays",
            "blackoutWeekends": "blackout_weekends",
            "advanceBooking": "advance_booking",
            "advanceBookingOther": "advance_booking_other",
            "notSuitableFor": "not_suitable_for",
            "importantInfo": "important_info",
            "cancellationPolicy": "cancellation_policy",
            "accessibilityInfo": "accessibility_info",
            "serviceTimeSlots": "service_time_slots",
            "imageUrls": "image_urls"  # Media field - can update directly
        }
        
        # Separate media and non-media changes
        media_fields = {"imageUrls"}
        requested_data = {}
        media_data = {}
        current_data_snapshot = {}
        changed_fields = []
        
        for pydantic_field, db_field in field_map.items():
            val = getattr(s, pydantic_field)
            if val is not None:
                current_val = current_service_data.get(db_field)
                # Only include if actually different
                if val != current_val:
                    if pydantic_field in media_fields:
                        media_data[db_field] = val
                    else:
                        requested_data[db_field] = val
                        current_data_snapshot[db_field] = current_val
                        changed_fields.append(pydantic_field)
        
        # Apply media changes directly
        if media_data:
            supabase_admin.table("vendor_services").update(media_data).eq("id", service_id).execute()
        
        # If no non-media changes, return success
        if not requested_data:
            return {"success": True, "message": "No changes detected or media updated", "pending_approval": False}
        
        # Create update request in MongoDB for non-media changes
        update_request = await chat_service.create_service_update_request(
            vendor_id=vendor_id,
            service_id=service_id,
            requested_by=current_user["id"],
            requested_by_name=current_user.get("name", current_user.get("email", "Vendor")),
            current_data=current_data_snapshot,
            requested_data=requested_data,
            changed_fields=changed_fields
        )
        
        if update_request:
            return {
                "success": True,
                "message": "Your service update request has been submitted for approval. You will be notified once it is reviewed.",
                "pending_approval": True,
                "request_id": update_request.get("id"),
                "changed_fields": changed_fields
            }
        else:
            # MongoDB not available - cannot create approval request
            logger.error("MongoDB not available - cannot create service approval request")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Approval service temporarily unavailable. Please try again later."
            )
        
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Update service error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/vendor/services/{service_id}")
async def delete_vendor_service(service_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "vendor":
        raise HTTPException(status_code=403, detail="Vendor access required")
    
    try:
        # Verify ownership
        vendor_res = supabase_admin.table("vendors").select("id").eq("user_id", current_user["id"]).single().execute()
        if not vendor_res.data:
            raise HTTPException(status_code=404, detail="Vendor profile not found")
        
        vendor_id = vendor_res.data["id"]
        
        # Delete if belongs to vendor
        res = supabase_admin.table("vendor_services").delete().eq("id", service_id).eq("vendor_id", vendor_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Service not found or access denied")
            
        return {"success": True, "message": "Service deleted successfully"}
        
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Delete service error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vendor/upload-file")
async def upload_vendor_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    service_id: Optional[str] = Form(None),
    current_user: dict = Depends(require_vendor)
):
    """
    Upload vendor files (documents, images, etc.)
    """
    try:
        # Get vendor id
        vendor_res = supabase_admin.table("vendors").select("id").eq("user_id", current_user["id"]).single().execute()
        if not vendor_res.data:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        vendor_id = vendor_res.data["id"]
        logger.info(f"Uploading file for vendor {vendor_id}, type: {file_type}")
        
        # Upload file to storage
        public_url = await upload_file_to_storage(file, vendor_id, file_type, service_id)
        
        # Update vendor record with file URL ONLY for Media Tab items (direct updates)
        # Documents (certificates, licenses) MUST go through profile update approval flow
        if file_type in ['logo', 'cover_image', 'promo_video']:
            column_map = {
                'logo': 'logo_url',
                'cover_image': 'cover_image_url',
                'promo_video': 'promo_video_url'
            }
            if file_type in column_map:
                supabase_admin.table("vendors").update({column_map[file_type]: public_url}).eq("id", vendor_id).execute()
        
        elif file_type == 'gallery':
            vendor_data = supabase_admin.table("vendors").select("gallery_urls").eq("id", vendor_id).single().execute()
            current_gallery = vendor_data.data.get("gallery_urls", []) if vendor_data.data else []
            # Safety check: ensure current_gallery is a list
            if not isinstance(current_gallery, list):
                current_gallery = []
            updated_gallery = current_gallery + [public_url]
            supabase_admin.table("vendors").update({"gallery_urls": updated_gallery}).eq("id", vendor_id).execute()
            
        elif file_type == 'service_image' and service_id:
            service_data = supabase_admin.table("vendor_services").select("image_urls").eq("id", service_id).single().execute()
            if service_data.data:
                current_images = service_data.data.get("image_urls", [])
                updated_images = current_images + [public_url]
                supabase_admin.table("vendor_services").update({"image_urls": updated_images}).eq("id", service_id).execute()
        
        return {
            "success": True,
            "url": public_url,
            "message": f"File uploaded successfully: {file.filename}"
        }
        
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@app.delete("/api/vendor/delete-file")
async def delete_vendor_file(
    data: DeleteFileSchema,
    current_user: dict = Depends(require_vendor)
):
    """
    Delete a vendor file (gallery image or service image)
    """
    try:
        vendor_id = data.vendor_id
        file_url = data.file_url
        file_type = data.file_type
        service_id = data.service_id
        
        # Verify ownership
        vendor_res = supabase_admin.table("vendors").select("id").eq("user_id", current_user["id"]).single().execute()
        if not vendor_res.data or vendor_res.data["id"] != vendor_id:
            raise HTTPException(status_code=403, detail="Access denied")

        if file_type == 'gallery':
            vendor_data = supabase_admin.table("vendors").select("gallery_urls").eq("id", vendor_id).single().execute()
            if vendor_data.data:
                gallery = vendor_data.data.get("gallery_urls", [])
                if file_url in gallery:
                    gallery.remove(file_url)
                    supabase_admin.table("vendors").update({"gallery_urls": gallery}).eq("id", vendor_id).execute()
        
        elif file_type == 'service_image' and service_id:
            service_data = supabase_admin.table("vendor_services").select("image_urls").eq("id", service_id).single().execute()
            if service_data.data:
                images = service_data.data.get("image_urls", [])
                if file_url in images:
                    images.remove(file_url)
                    supabase_admin.table("vendor_services").update({"image_urls": images}).eq("id", service_id).execute()
        
        # We don't delete from storage yet to keep it simple, just remove from DB list
        return {"success": True, "message": "File removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")


# ==================== CHAT ENDPOINTS ====================

@app.post("/api/chat/messages/{vendor_id}")
async def send_chat_message(
    vendor_id: str,
    data: ChatMessageSchema,
    current_user: dict = Depends(get_current_user)
):
    """Send a chat message (vendor to admin or admin to vendor)"""
    try:

        user_role = current_user.get("role")
        sender = "vendor" if user_role == "vendor" else "admin"
        
        # Verify vendor access for vendor role
        if user_role == "vendor":
            vendor_res = supabase_admin.table("vendors").select("id").eq("user_id", current_user["id"]).single().execute()
            if not vendor_res.data or vendor_res.data["id"] != vendor_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        message = await chat_service.create_message(
            vendor_id=vendor_id,
            sender=sender,
            sender_id=current_user["id"],
            sender_name=current_user.get("name", current_user.get("email", "Unknown")),
            message=data.message,
            message_type="text",
            attachments=data.attachments
        )
        
        if message:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=500, detail="Failed to send message - chat service unavailable")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send chat message error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/messages/{vendor_id}")
async def get_chat_messages(
    vendor_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = 100,
    skip: int = 0
):
    """Get chat messages for a specific vendor"""
    try:

        user_role = current_user.get("role")
        
        # Verify access
        if user_role == "vendor":
            vendor_res = supabase_admin.table("vendors").select("id").eq("user_id", current_user["id"]).single().execute()
            if not vendor_res.data or vendor_res.data["id"] != vendor_id:
                raise HTTPException(status_code=403, detail="Access denied")
        elif user_role not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        messages = await chat_service.get_messages_by_vendor(vendor_id, limit, skip)
        
        # Mark messages as read
        reader = "vendor" if user_role == "vendor" else "admin"
        await chat_service.mark_messages_read(vendor_id, reader)
        
        return {"success": True, "messages": messages}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get chat messages error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/chat/unread-count", dependencies=[Depends(require_staff)])
async def get_unread_count():
    """Get count of unread messages from vendors"""
    try:
        count = await chat_service.get_unread_count_for_admin()
        return {"success": True, "unread_count": count}
    except Exception as e:
        logger.error(f"Get unread count error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/chat/summary", dependencies=[Depends(require_staff)])
async def get_chat_summary():
    """Get summary of all vendor chats for admin"""
    try:
        summary = await chat_service.get_admin_chat_summary()
        return {"success": True, "summary": summary}
    except Exception as e:
        logger.error(f"Get chat summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vendor/chat/unread-count")
async def get_vendor_unread_count(
    current_user: dict = Depends(require_vendor)
):
    """Get count of unread messages for current vendor from admin"""
    try:
        # Get vendor id
        vendor_res = supabase_admin.table("vendors").select("id").eq("user_id", current_user["id"]).single().execute()
        if not vendor_res.data:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        vendor_id = vendor_res.data["id"]
        count = await chat_service.get_unread_count_for_vendor(vendor_id)
        return {"success": True, "unread_count": count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get vendor unread count error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== UPDATE REQUEST ENDPOINTS ====================

@app.get("/api/admin/update-requests", dependencies=[Depends(require_staff)])
async def get_update_requests(
    status: Optional[str] = None,
    vendor_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
):
    """Get update requests (for admin/manager approval)"""
    try:
        if status == "pending" or vendor_id:
            requests = await chat_service.get_pending_update_requests(vendor_id, limit, skip)
        else:
            requests = await chat_service.get_all_update_requests(status, limit, skip)
        
        return {"success": True, "requests": requests, "count": len(requests)}
        
    except Exception as e:
        logger.error(f"Get update requests error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/update-requests/{request_id}", dependencies=[Depends(require_staff)])
async def get_update_request_detail(request_id: str):
    """Get a specific update request by ID"""
    try:
        request = await chat_service.get_update_request_by_id(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Update request not found")
        
        return {"success": True, "request": request}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get update request detail error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/update-requests/{request_id}/approve", dependencies=[Depends(require_staff)])
async def approve_update_request(
    request_id: str,
    current_user: dict = Depends(require_staff)
):
    """Approve a vendor update request and apply changes"""
    try:
        # Get the request first
        request = await chat_service.get_update_request_by_id(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Update request not found")
        
        if request.get("status") != "pending":
            raise HTTPException(status_code=400, detail=f"Request already {request.get('status')}")
        
        # Approve the request
        approved_request = await chat_service.approve_update_request(
            request_id=request_id,
            reviewed_by=current_user["id"],
            reviewed_by_name=current_user.get("name", current_user.get("email", "Admin"))
        )
        
        if not approved_request:
            raise HTTPException(status_code=500, detail="Failed to approve request")
        
        return {
            "success": True,
            "message": "Update request approved and changes applied",
            "request": approved_request
        }

        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve update request error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/update-requests/{request_id}/reject", dependencies=[Depends(require_staff)])
async def reject_update_request(
    request_id: str,
    data: UpdateRequestRejectionSchema,
    current_user: dict = Depends(require_staff)
):
    """Reject a vendor update request with a reason"""
    try:
        # Get the request first
        request = await chat_service.get_update_request_by_id(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Update request not found")
        
        if request.get("status") != "pending":
            raise HTTPException(status_code=400, detail=f"Request already {request.get('status')}")
        
        # Reject the request
        rejected_request = await chat_service.reject_update_request(
            request_id=request_id,
            reviewed_by=current_user["id"],
            reviewed_by_name=current_user.get("name", current_user.get("email", "Admin")),
            reason=data.reason
        )
        
        if not rejected_request:
            raise HTTPException(status_code=500, detail="Failed to reject request")
        
        return {
            "success": True,
            "message": "Update request rejected",
            "request": rejected_request
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reject update request error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vendor/update-requests")
async def get_vendor_update_requests(
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    limit: int = 20,
    skip: int = 0
):
    """Get update requests for the current vendor"""
    if current_user.get("role") != "vendor":
        raise HTTPException(status_code=403, detail="Vendor access required")
    
    try:
        # Get vendor ID
        vendor_res = supabase_admin.table("vendors").select("id").eq("user_id", current_user["id"]).single().execute()
        if not vendor_res.data:
            raise HTTPException(status_code=404, detail="Vendor profile not found")
        
        vendor_id = vendor_res.data["id"]
        
        if status == "pending":
            requests = await chat_service.get_pending_update_requests(vendor_id, limit, skip)
        else:
            # Get all requests for this vendor
            from app.database.mongo_config import get_update_requests_collection
            collection = await get_update_requests_collection()
            if collection:
                query = {"vendor_id": vendor_id}
                if status:
                    query["status"] = status
                
                cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
                requests = []
                async for doc in cursor:
                    requests.append(chat_service._serialize_update_request(doc))
            else:
                requests = []
        
        return {"success": True, "requests": requests, "count": len(requests)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get vendor update requests error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

