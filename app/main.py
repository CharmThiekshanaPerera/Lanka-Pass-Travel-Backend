# main.py
from __future__ import annotations
from fastapi import FastAPI, HTTPException, status, UploadFile, Form, File
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8080",
        # Add your local network IP if testing from mobile
        "*" 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class ServiceData(BaseModel):
    serviceName: str
    serviceCategory: str
    shortDescription: str
    whatsIncluded: Optional[str] = None
    whatsNotIncluded: Optional[str] = None
    durationValue: int
    durationUnit: str
    languagesOffered: List[str] = []
    groupSizeMin: int = 1
    groupSizeMax: int = 10
    dailyCapacity: Optional[int] = None
    operatingDays: List[str] = []
    locationsCovered: List[str] = []
    retailPrice: float
    currency: str = "LKR"
    notSuitableFor: Optional[str] = None
    importantInfo: Optional[str] = None
    cancellationPolicy: Optional[str] = None
    accessibilityInfo: Optional[str] = None

class VendorRegistrationRequest(BaseModel):
    # Step 1: Vendor Basics
    vendorType: str
    vendorTypeOther: Optional[str] = None
    businessName: str
    legalName: Optional[str] = None
    contactPerson: str
    email: EmailStr
    phoneNumber: str
    operatingAreas: List[str]
    operatingAreasOther: Optional[str] = None
    
    # Step 2: Business Details
    businessRegNumber: Optional[str] = None
    businessAddress: str
    taxId: Optional[str] = None
    
    # Step 3: Service Details
    services: List[ServiceData]
    
    # Step 6: Payment Details
    bankName: str
    bankNameOther: Optional[str] = None
    accountHolderName: str
    accountNumber: str
    bankBranch: str
    
    # Step 7: Agreements
    acceptTerms: bool
    acceptCommission: bool
    acceptCancellation: bool
    grantRights: bool
    confirmAccuracy: bool
    marketingPermission: bool

    # Account Details
    password: str

class FileUploadRequest(BaseModel):
    vendor_id: str
    file_type: str
    service_index: Optional[int] = None  # For service images

# Helper Functions
def generate_secure_password():
    """Generate a secure random password"""
    return str(uuid.uuid4()).replace('-', '')[:12]

def upload_file_to_storage(file: UploadFile, vendor_id: str, file_type: str, service_index: Optional[int] = None):
    """Upload file to Supabase Storage"""
    try:
        # Read file content
        content = file.file.read()
        
        # Generate unique filename
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        
        # Determine file path
        if service_index is not None:
            file_path = f"vendors/{vendor_id}/services/{service_index}/{unique_filename}"
        else:
            file_path = f"vendors/{vendor_id}/{file_type}/{unique_filename}"
        
        # Upload to storage
        result = supabase.storage.from_("vendor-files").upload(
            file_path,
            content,
            {"content-type": file.content_type}
        )
        
        # Get public URL
        public_url = supabase.storage.from_("vendor-files").get_public_url(file_path)
        
        return public_url
        
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Lanka Pass Travel API is running"}

@app.post("/api/vendor/register", status_code=status.HTTP_201_CREATED)
async def register_vendor(vendor_data: VendorRegistrationRequest):
    """
    Register a new vendor with services
    """
    try:
        logger.info(f"Starting vendor registration for: {vendor_data.email}")
        
        # 1. Check if email already exists in users table
        existing_user = supabase.table("users").select("*").eq("email", vendor_data.email).execute()
        
        user_id = None
        if existing_user.data:
            user_id = existing_user.data[0]["id"]
            logger.info(f"User already exists in users table: {user_id}")
        else:
            # Check if user exists in Supabase Auth (but not in users table)
            # This helps if previous test runs failed halfway
            logger.info(f"Checking if user exists in Supabase Auth: {vendor_data.email}")
            try:
                auth_list_res = supabase.auth.admin.list_users()
                # Handle different return formats (list vs object with .users)
                users_to_check = auth_list_res.users if hasattr(auth_list_res, 'users') else auth_list_res
                
                for u in users_to_check:
                    if u.email == vendor_data.email:
                        user_id = u.id
                        logger.info(f"Found existing auth user: {user_id}")
                        break
            except Exception as list_err:
                logger.warning(f"Could not list users from Auth: {list_err}. Proceeding with creation attempt.")
            
            if not user_id:
                # Create auth user using Admin API (since we have service role key)
                # Use password provided in request
                admin_user_params = {
                    "email": str(vendor_data.email),
                    "password": vendor_data.password,
                    "email_confirm": True,
                    "user_metadata": {
                        "name": vendor_data.contactPerson,
                        "role": "vendor",
                        "business_name": vendor_data.businessName
                    }
                }
                logger.info(f"Creating auth user via Admin API for: {admin_user_params['email']}")
                
                try:
                    auth_response = supabase.auth.admin.create_user(admin_user_params)
                    if not auth_response.user:
                        raise Exception("Auth user creation returned no user object")
                    user_id = auth_response.user.id
                except Exception as auth_err:
                    error_str = str(auth_err)
                    logger.error(f"Auth creation failed: {error_str}")
                    
                    if "rate limit" in error_str.lower():
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Supabase rate limit exceeded. Please wait a few minutes or increase your rate limits in Supabase Dashboard (Authentication -> Auth Settings)."
                        )
                    
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to create authentication user: {error_str}"
                    )
            
            # Ensure user record exists in public.users table
            # We use upsert or check again to be safe
            user_record = {
                "id": user_id,
                "email": str(vendor_data.email),
                "name": vendor_data.contactPerson,
                "role": "vendor",
                "is_active": True
            }
            
            try:
                # Check if we need to insert into users table (in case it wasn't there)
                check_user = supabase.table("users").select("id").eq("id", user_id).execute()
                if not check_user.data:
                    supabase.table("users").insert(user_record).execute()
                    logger.info(f"Inserted user record into users table: {user_id}")
            except Exception as e:
                logger.warning(f"Note: Users table insertion skipped or failed (might already exist): {e}")
        
        # 2. Check if vendor profile already exists
        existing_vendor = supabase.table("vendors").select("*").eq("user_id", user_id).execute()
        
        if existing_vendor.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vendor profile already exists for this user"
            )
        
        # 3. Create vendor profile
        vendor_profile = {
            "user_id": user_id,
            "vendor_type": vendor_data.vendorType,
            "vendor_type_other": vendor_data.vendorTypeOther,
            "business_name": vendor_data.businessName,
            "legal_name": vendor_data.legalName,
            "contact_person": vendor_data.contactPerson,
            "email": vendor_data.email,
            "phone_number": vendor_data.phoneNumber,
            "operating_areas": vendor_data.operatingAreas,
            "operating_areas_other": vendor_data.operatingAreasOther,
            "business_reg_number": vendor_data.businessRegNumber,
            "business_address": vendor_data.businessAddress,
            "tax_id": vendor_data.taxId,
            "bank_name": vendor_data.bankName,
            "bank_name_other": vendor_data.bankNameOther,
            "account_holder_name": vendor_data.accountHolderName,
            "account_number": vendor_data.accountNumber,
            "bank_branch": vendor_data.bankBranch,
            "accept_terms": vendor_data.acceptTerms,
            "accept_commission": vendor_data.acceptCommission,
            "accept_cancellation": vendor_data.acceptCancellation,
            "grant_rights": vendor_data.grantRights,
            "confirm_accuracy": vendor_data.confirmAccuracy,
            "marketing_permission": vendor_data.marketingPermission,
            "status": "pending"
        }
        
        vendor_result = supabase.table("vendors").insert(vendor_profile).execute()
        
        if not vendor_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create vendor profile"
            )
        
        vendor_id = vendor_result.data[0]["id"]
        logger.info(f"Created vendor profile: {vendor_id}")
        
        # 4. Create services
        for index, service in enumerate(vendor_data.services):
            service_record = {
                "vendor_id": vendor_id,
                "service_name": service.serviceName,
                "service_category": service.serviceCategory,
                "short_description": service.shortDescription,
                "whats_included": service.whatsIncluded,
                "whats_not_included": service.whatsNotIncluded,
                "duration_value": service.durationValue,
                "duration_unit": service.durationUnit,
                "languages_offered": service.languagesOffered,
                "group_size_min": service.groupSizeMin,
                "group_size_max": service.groupSizeMax,
                "daily_capacity": service.dailyCapacity,
                "operating_days": service.operatingDays,
                "locations_covered": service.locationsCovered,
                "retail_price": service.retailPrice,
                "currency": service.currency,
                "not_suitable_for": service.notSuitableFor,
                "important_info": service.importantInfo,
                "cancellation_policy": service.cancellationPolicy,
                "accessibility_info": service.accessibilityInfo
            }
            
            service_result = supabase.table("vendor_services").insert(service_record).execute()
            logger.info(f"Created service {index + 1} for vendor {vendor_id}")
        
        # 5. Send welcome email (placeholder - implement your email service)
        # send_welcome_email(vendor_data.email, vendor_data.contactPerson)
        
        return {
            "success": True,
            "message": "Vendor registration submitted successfully!",
            "vendor_id": vendor_id,
            "user_id": user_id,
            "status": "pending",
            "next_steps": "Our team will review your application within 2-3 business days."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vendor registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vendor registration failed: {str(e)}"
        )

@app.post("/api/vendor/upload-file")
async def upload_vendor_file(
    file: UploadFile = File(...),
    vendor_id: str = Form(...),
    file_type: str = Form(...),
    service_index: Optional[int] = Form(None)
):
    """
    Upload vendor files (documents, images, etc.)
    """
    try:
        logger.info(f"Uploading file: {file.filename} for vendor {vendor_id}, type: {file_type}")
        
        # Validate file type
        valid_file_types = [
            'reg_certificate', 'nic_passport', 'tourism_license',
            'logo', 'cover_image', 'gallery'
        ]
        
        if file_type not in valid_file_types and not file_type.startswith('service_'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Must be one of: {', '.join(valid_file_types)} or 'service_[index]'"
            )
        
        # Upload file to storage
        public_url = upload_file_to_storage(file, vendor_id, file_type, service_index)
        
        # Update vendor record with file URL
        if file_type in ['reg_certificate', 'nic_passport', 'tourism_license', 'logo', 'cover_image']:
            # Map file_type to database column name
            column_map = {
                'reg_certificate': 'reg_certificate_url',
                'nic_passport': 'nic_passport_url',
                'tourism_license': 'tourism_license_url',
                'logo': 'logo_url',
                'cover_image': 'cover_image_url'
            }
            
            if file_type in column_map:
                update_data = {column_map[file_type]: public_url}
                supabase.table("vendors").update(update_data).eq("id", vendor_id).execute()
        
        elif file_type == 'gallery':
            # Get current gallery URLs
            vendor_data = supabase.table("vendors").select("gallery_urls").eq("id", vendor_id).execute()
            current_gallery = vendor_data.data[0]["gallery_urls"] if vendor_data.data else []
            
            # Add new URL to gallery
            updated_gallery = current_gallery + [public_url] if current_gallery else [public_url]
            supabase.table("vendors").update({"gallery_urls": updated_gallery}).eq("id", vendor_id).execute()
        
        elif file_type.startswith('service_'):
            # Handle service images
            if service_index is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="service_index is required for service images"
                )
            
            # Get service for this vendor
            services_data = supabase.table("vendor_services").select("*").eq("vendor_id", vendor_id).execute()
            
            if services_data.data and len(services_data.data) > service_index:
                service_id = services_data.data[service_index]["id"]
                current_images = services_data.data[service_index].get("image_urls", [])
                
                # Add new image URL
                updated_images = current_images + [public_url] if current_images else [public_url]
                supabase.table("vendor_services").update({"image_urls": updated_images}).eq("id", service_id).execute()
        
        return {
            "success": True,
            "url": public_url,
            "message": f"File uploaded successfully: {file.filename}"
        }
        
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )

@app.get("/api/vendor/{vendor_id}")
async def get_vendor(vendor_id: str):
    """
    Get vendor details by ID
    """
    try:
        # Get vendor data
        vendor_data = supabase.table("vendors").select("*").eq("id", vendor_id).execute()
        
        if not vendor_data.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        # Get vendor services
        services_data = supabase.table("vendor_services").select("*").eq("vendor_id", vendor_id).execute()
        
        return {
            "success": True,
            "vendor": vendor_data.data[0],
            "services": services_data.data if services_data.data else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch vendor data: {str(e)}"
        )

@app.get("/api/vendors")
async def get_vendors(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """
    Get all vendors with optional filtering
    """
    try:
        query = supabase.table("vendors").select("*")
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("created_at", desc=True)
        query = query.range(skip, skip + limit - 1)
        
        vendors_data = query.execute()
        
        return {
            "success": True,
            "vendors": vendors_data.data if vendors_data.data else [],
            "count": len(vendors_data.data) if vendors_data.data else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch vendors: {str(e)}"
        )

@app.put("/api/vendor/{vendor_id}/status")
async def update_vendor_status(
    vendor_id: str,
    status: str,
    reason: Optional[str] = None
):
    """
    Update vendor status (admin only)
    """
    try:
        valid_statuses = ["pending", "approved", "rejected", "suspended"]
        
        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        update_data = {"status": status}
        if reason:
            update_data["status_reason"] = reason
        
        result = supabase.table("vendors").update(update_data).eq("id", vendor_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        return {
            "success": True,
            "message": f"Vendor status updated to {status}",
            "vendor": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vendor status: {str(e)}"
        )

# Unified Auth Endpoints
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/api/auth/login")
async def login(login_data: LoginRequest):
    """
    Login endpoint using Supabase Auth
    """
    try:
        logger.info(f"Login attempt for: {login_data.email}")
        
        # Sign in with password
        auth_response = supabase.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Get user details from public.users table
        user_data = supabase.table("users").select("*").eq("id", auth_response.user.id).execute()
        user_profile = user_data.data[0] if user_data.data else {
            "id": auth_response.user.id,
            "email": auth_response.user.email,
            "name": auth_response.user.user_metadata.get("name", ""),
            "role": auth_response.user.user_metadata.get("role", "user")
        }
        
        return {
            "success": True,
            "access_token": auth_response.session.access_token,
            "token_type": "bearer",
            "user": user_profile
        }
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
