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
import io
import csv
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client, Client
import logging
from app.services.sms_service import SmsService


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL", "").strip()
supabase_key = os.getenv("SUPABASE_KEY", "").strip()
print(f"BOOT: SUPABASE_URL={supabase_url}")
if supabase_key:
    print(f"BOOT: SUPABASE_KEY starts with: {supabase_key[:15]}...")
else:
    print("BOOT: SUPABASE_KEY is MISSING!")
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

class ServiceSchema(BaseModel):
    serviceName: str
    serviceCategory: str
    serviceDescription: Optional[str] = None
    description: Optional[str] = None
    shortDescription: Optional[str] = None
    whatsIncluded: Optional[str] = None
    whatsNotIncluded: Optional[str] = None
    durationValue: Optional[int] = None
    durationUnit: Optional[str] = None
    languagesOffered: Optional[List[str]] = []
    groupSizeMin: Optional[int] = None
    groupSizeMax: Optional[int] = None
    dailyCapacity: Optional[int] = None
    operatingDays: Optional[List[str]] = []
    locationsCovered: Optional[List[str]] = []
    currency: str = "USD"
    retailPrice: float
    # New fields
    operatingHoursFrom: Optional[str] = None
    operatingHoursTo: Optional[str] = None
    blackoutDates: Optional[List[str]] = []
    blackoutHolidays: Optional[bool] = False
    notSuitableFor: Optional[str] = None
    importantInfo: Optional[str] = None
    cancellationPolicy: Optional[str] = None
    accessibilityInfo: Optional[str] = None
    imageUrls: Optional[List[str]] = []

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
    payoutCycle: Optional[str] = None
    payoutDate: Optional[str] = None
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
    payoutCycle: Optional[str] = None
    payoutDate: Optional[str] = None

# OTP Endpoints
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


# File Upload API
@app.post("/api/vendor/upload-file")
async def upload_file(
    file: UploadFile = File(...), 
    file_type: str = Form(...),
    vendor_id: str = Form(...),
    service_index: str = Form(None)
):
    try:
        file_ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
        file_name = f"{file_type}_{uuid.uuid4()}.{file_ext}"
        bucket_name = "vendor-docs"
        
        content = await file.read()
        
        try:
            supabase_admin.storage.from_(bucket_name).upload(
                path=file_name,
                file=content,
                file_options={"content-type": file.content_type}
            )
        except Exception as upload_err:
            logger.error(f"Storage upload failed: {str(upload_err)}")
            if "Bucket not found" in str(upload_err):
                 raise HTTPException(status_code=404, detail="Storage bucket 'vendor-docs' not found.")
            raise HTTPException(status_code=500, detail=f"Failed to upload: {str(upload_err)}")
            
        project_url = os.getenv("SUPABASE_URL").rstrip("/")
        public_url = f"{project_url}/storage/v1/object/public/{bucket_name}/{file_name}"
        
        try:
            update_data = {}
            if file_type == "logo": update_data["logo_url"] = public_url
            elif file_type == "cover_image": update_data["cover_image_url"] = public_url
            elif file_type == "reg_certificate": update_data["reg_certificate_url"] = public_url
            elif file_type == "nic_passport": update_data["nic_passport_url"] = public_url
            elif file_type == "tourism_license": update_data["tourism_license_url"] = public_url
            elif file_type == "gallery":
                current_vendor = supabase_admin.table("vendors").select("gallery_urls").eq("id", vendor_id).single().execute()
                urls = current_vendor.data.get("gallery_urls") or []
                urls.append(public_url)
                update_data["gallery_urls"] = urls
            elif file_type.startswith("service_") and service_index is not None:
                idx = int(service_index)
                srv_res = supabase_admin.table("vendor_services").select("*").eq("vendor_id", vendor_id).execute()
                if srv_res.data and len(srv_res.data) > idx:
                    tid = srv_res.data[idx]["id"]
                    imgs = srv_res.data[idx].get("image_urls") or []
                    imgs.append(public_url)
                    supabase_admin.table("vendor_services").update({"image_urls": imgs}).eq("id", tid).execute()
            
            if update_data:
                supabase_admin.table("vendors").update(update_data).eq("id", vendor_id).execute()
        except Exception as db_err:
            logger.error(f"DB update failed for file: {str(db_err)}")
        
        return {"success": True, "url": public_url}
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Vendor API
@app.post("/api/vendor/register", status_code=201)
async def register_vendor(data: VendorRegisterRequest):
    user_id = None
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
        except Exception as e:
            logger.error(f"Profile creation failed: {str(e)}")
            supabase_admin.auth.admin.delete_user(user_id)
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
                "payout_cycle": data.payoutCycle,
                "payout_date": data.payoutDate,
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
        except Exception as e:
            logger.error(f"Vendor profile error: {str(e)}")
            supabase_admin.table("users").delete().eq("id", user_id).execute()
            supabase_admin.auth.admin.delete_user(user_id)
            raise HTTPException(status_code=500, detail=f"Vendor profile failed: {str(e)}")
        
        # 4. Services
        for s in data.services:
            try:
                db_service = {
                    "vendor_id": vendor_id,
                    "service_name": s.serviceName,
                    "service_category": s.serviceCategory,
                    "service_description": s.serviceDescription or s.description,
                    "short_description": s.shortDescription,
                    "whats_included": s.whatsIncluded,
                    "whats_not_included": s.whatsNotIncluded,
                    "duration_value": s.durationValue,
                    "duration_unit": s.durationUnit,
                    "languages_offered": s.languagesOffered,
                    "group_size_min": s.groupSizeMin,
                    "group_size_max": s.groupSizeMax,
                    "daily_capacity": s.dailyCapacity, # Fixed Typo
                    "operating_days": s.operatingDays,
                    "locations_covered": s.locationsCovered,
                    "currency": s.currency,
                    "retail_price": s.retailPrice,
                    "commission": 0,
                    "net_price": s.retailPrice,
                    # New fields
                    "operating_hours_from": s.operatingHoursFrom,
                    "operating_hours_to": s.operatingHoursTo,
                    "blackout_dates": s.blackoutDates,
                    "blackout_holidays": s.blackoutHolidays,
                    "not_suitable_for": s.notSuitableFor,
                    "important_info": s.importantInfo,
                    "cancellation_policy": s.cancellationPolicy,
                    "accessibility_info": s.accessibilityInfo,
                    "image_urls": s.imageUrls
                }
                supabase_admin.table("vendor_services").insert(db_service).execute()
            except Exception as se:
                logger.error(f"Service insert error for {s.serviceName}: {str(se)}")
                # Re-raise to ensure we don't return success if services fail
                raise HTTPException(status_code=500, detail=f"Service registration failed for {s.serviceName}: {str(se)}")
                
        return {"success": True, "vendor_id": vendor_id}
    except HTTPException: raise
    except Exception as e:
        logger.exception("Vendor registration exception")
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
    if current_user.get("role") != "vendor":
        raise HTTPException(status_code=403, detail="Vendor access required")
    
    try:
        # Get vendor ID first
        vendor_res = supabase_admin.table("vendors").select("id").eq("user_id", current_user["id"]).single().execute()
        if not vendor_res.data:
            raise HTTPException(status_code=404, detail="Vendor profile not found")
        
        vendor_id = vendor_res.data["id"]
        
        # Prepare update data (only non-None fields)
        update_data = {}
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
            "payoutCycle": "payout_cycle",
            "payoutDate": "payout_date"
        }
        
        for pydantic_field, db_field in field_map.items():
            val = getattr(data, pydantic_field)
            if val is not None:
                update_data[db_field] = val
        
        if update_data:
            res = supabase_admin.table("vendors").update(update_data).eq("id", vendor_id).execute()
            
            # Also update name in users table if contactPerson changed
            if "contact_person" in update_data:
                supabase_admin.table("users").update({"name": update_data["contact_person"]}).eq("id", current_user["id"]).execute()
            
            return {"success": True, "vendor": res.data[0]}
        
        return {"success": True, "message": "No changes requested"}
        
    except Exception as e:
        logger.error(f"Update vendor profile error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Removed redundant get_vendors endpoint

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
