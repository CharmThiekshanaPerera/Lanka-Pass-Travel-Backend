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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
print(f"BOOT: SUPABASE_URL={supabase_url}")
if supabase_key:
    print(f"BOOT: SUPABASE_KEY starts with: {supabase_key[:15]}...")
else:
    print("BOOT: SUPABASE_KEY is MISSING!")
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
        user_email = auth_res.user.email
        user_role = auth_res.user.user_metadata.get("role", "user") if auth_res.user.user_metadata else "user"
        user_name = auth_res.user.user_metadata.get("name", "") if auth_res.user.user_metadata else ""

        try:
            # Try to get extended profile, but don't fail if RLS/Recursion occurs
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
        logger.exception("Login failed with exception")
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")

@app.post("/api/auth/register")
async def register(request: Request):
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        name = data.get("name")
        role = data.get("role", "user")
        
        # Use regular sign_up for non-admin roles
        if role in ["user", "vendor"]:
            # Create auth user using sign_up
            auth_res = supabase.auth.sign_up({
                "email": str(email),
                "password": password,
                "options": {
                    "data": {"role": role, "name": name}
                }
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
            
            # Sign in to get session
            login_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            
            return {
                "access_token": login_res.session.access_token,
                "token_type": "bearer",
                "user": user_profile
            }
        else:
            # For admin/manager roles, use admin API (requires service_role key)
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
        logger.exception("Registration failed with exception")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

# Admin API
@app.get("/api/admin/dashboard", dependencies=[Depends(require_staff)])
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

@app.get("/api/admin/vendors", dependencies=[Depends(require_staff)])
async def get_all_vendors():
    try:
        vendors = supabase.table("vendors").select("*").execute()
        return {"success": True, "vendors": vendors.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/vendors/{vendor_id}", dependencies=[Depends(require_staff)])
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

@app.patch("/api/admin/vendors/{vendor_id}", dependencies=[Depends(require_staff)])
async def update_vendor_status(vendor_id: str, request: Request):
    data = await request.json()
    res = supabase.table("vendors").update({
        "status": data.get("status"),
        "status_reason": data.get("status_reason")
    }).eq("id", vendor_id).execute()
    return {"success": True, "vendor": res.data[0]}

# Manager Management (Admin Only)
@app.get("/api/admin/managers", dependencies=[Depends(require_admin)])
async def get_managers():
    try:
        users = supabase.table("users").select("*").eq("role", "manager").execute()
        return {"success": True, "managers": users.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/managers", dependencies=[Depends(require_admin)])
async def create_manager(request: Request):
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        name = data.get("name")
        
        # Create auth user
        auth_res = supabase.auth.admin.create_user({
            "email": str(email),
            "password": password,
            "email_confirm": True,
            "user_metadata": {"role": "manager", "name": name}
        })
        user_id = auth_res.user.id
        
        # Create public user
        user_profile = {
            "id": user_id,
            "email": str(email),
            "name": name,
            "role": "manager",
            "is_active": True
        }
        supabase.table("users").insert(user_profile).execute()
        
        return {"success": True, "manager": user_profile}
    except Exception as e:
        logger.error(f"Create manager error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create manager: {str(e)}")

@app.delete("/api/admin/managers/{user_id}", dependencies=[Depends(require_admin)])
async def delete_manager(user_id: str):
    try:
        # Delete from public users first (cascade should handle it if set up, but let's be safe)
        # Actually deleting from auth.users usually cascades to public.users if configured in DB
        # But supabase-py client mainly interacts with public schema.
        # We need to use admin api to delete user from auth.
        
        res = supabase.auth.admin.delete_user(user_id)
        # Also clean up public table if cascade isn't automatic (it is in schema.sql but...)
        supabase.table("users").delete().eq("id", user_id).execute()
        
        return {"success": True, "message": "Manager deleted"}
    except Exception as e:
        logger.error(f"Delete manager error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete manager: {str(e)}")

# Export Data (Staff Only)
@app.get("/api/admin/export/vendors", dependencies=[Depends(require_staff)])
async def export_vendors():
    try:
        # Fetch all vendor data
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
        # Generate unique filename
        file_ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
        file_name = f"{file_type}_{uuid.uuid4()}.{file_ext}"
        bucket_name = "vendor-docs"
        
        # Read file content
        content = await file.read()
        
        # Upload to Supabase Storage
        try:
            res = supabase.storage.from_(bucket_name).upload(
                path=file_name,
                file=content,
                file_options={"content-type": file.content_type}
            )
        except Exception as upload_err:
            logger.error(f"Storage upload failed: {str(upload_err)}")
            if "Bucket not found" in str(upload_err):
                 raise HTTPException(status_code=404, detail="Storage bucket 'vendor-docs' not found. Please create it in Supabase.")
            raise HTTPException(status_code=500, detail=f"Failed to upload to storage: {str(upload_err)}")
            
        # Construct Public URL
        project_url = os.getenv("SUPABASE_URL")
        # Remove trailing slash if present
        if project_url.endswith("/"):
            project_url = project_url[:-1]
            
        public_url = f"{project_url}/storage/v1/object/public/{bucket_name}/{file_name}"
        
        # UPDATE DATABASE RECORD
        # We update the vendor record directly because the frontend might not save the URL
        try:
            update_data = {}
            
            if file_type == "logo":
                update_data["logo_url"] = public_url
            elif file_type == "cover_image":
                update_data["cover_image_url"] = public_url
            elif file_type == "reg_certificate":
                update_data["reg_certificate_url"] = public_url
            elif file_type == "nic_passport":
                update_data["nic_passport_url"] = public_url
            elif file_type == "tourism_license":
                update_data["tourism_license_url"] = public_url
            elif file_type == "gallery":
                # For array, we need to fetch first or use postgres append
                # Simple fetch-append-update for safety
                current_vendor = supabase.table("vendors").select("gallery_urls").eq("id", vendor_id).single().execute()
                current_urls = current_vendor.data.get("gallery_urls") or []
                current_urls.append(public_url)
                update_data["gallery_urls"] = current_urls
            
            if update_data:
                supabase.table("vendors").update(update_data).eq("id", vendor_id).execute()
                logger.info(f"Updated vendor {vendor_id} with {file_type} url: {public_url}")
                
        except Exception as db_err:
            logger.error(f"Failed to update database with file URL: {str(db_err)}")
            # We don't fail the request, just log it, as the file was uploaded
        
        return {"success": True, "url": public_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Vendor API
@app.post("/api/vendor/register", status_code=201)
async def register_vendor(request: Request):
    user_id = None
    try:
        data = await request.json()
        logger.info(f"Vendor registration started for email: {data.get('email')}")
        
        # 1. Create Auth User using Admin API (bypasses rate limits)
        try:
            auth_res = supabase.auth.admin.create_user({
                "email": data.get("email"),
                "password": data.get("password"),
                "email_confirm": True,  # Auto-confirm email
                "user_metadata": {
                    "role": "vendor", 
                    "name": data.get("contactPerson")
                }
            })
            user_id = auth_res.user.id
            logger.info(f"Auth user created via Admin API with ID: {user_id}")
        except Exception as e:
            logger.error(f"Auth user creation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create auth user: {str(e)}")
        
        # 2. Create Public User
        try:
            user_insert_result = supabase.table("users").insert({
                "id": user_id,
                "email": data.get("email"),
                "name": data.get("contactPerson"),
                "role": "vendor"
            }).execute()
            logger.info(f"Public user created: {user_insert_result.data}")
        except Exception as e:
            logger.error(f"Public user creation failed: {str(e)}")
            # Try to clean up auth user
            try:
                supabase.auth.admin.delete_user(user_id)
            except:
                pass
            raise HTTPException(status_code=500, detail=f"Failed to create user profile: {str(e)}")
        
        # 3. Create Vendor Profile
        try:
            db_vendor = {
                "user_id": user_id,
                "vendor_type": data.get("vendorType"),
                "vendor_type_other": data.get("vendorTypeOther"),
                "business_name": data.get("businessName"),
                "legal_name": data.get("legalName"),
                "contact_person": data.get("contactPerson"),
                "email": data.get("email"),
                "phone_number": data.get("phoneNumber"),
                "phone_verified": data.get("phoneVerified", False),
                "operating_areas": data.get("operatingAreas"),
                "operating_areas_other": data.get("operatingAreasOther"),
                "business_reg_number": data.get("businessRegNumber"),
                "business_address": data.get("businessAddress"),
                "tax_id": data.get("taxId"),
                "bank_name": data.get("bankName"),
                "bank_name_other": data.get("bankNameOther"),
                "account_holder_name": data.get("accountHolderName"),
                "account_number": data.get("accountNumber"),
                "bank_branch": data.get("bankBranch"),
                # File URLs
                "reg_certificate_url": data.get("regCertificateUrl"),
                "nic_passport_url": data.get("nicPassportUrl"),
                "tourism_license_url": data.get("tourismLicenseUrl"),
                "logo_url": data.get("logoUrl"),
                "cover_image_url": data.get("coverImageUrl"),
                "gallery_urls": data.get("galleryUrls", []),
                # Agreements
                "accept_terms": data.get("acceptTerms", False),
                "accept_commission": data.get("acceptCommission", False),
                "accept_cancellation": data.get("acceptCancellation", False),
                "grant_rights": data.get("grantRights", False),
                "confirm_accuracy": data.get("confirmAccuracy", False),
                "status": "pending"
            }
            
            logger.info(f"Attempting to create vendor profile for user_id: {user_id}")
            res = supabase.table("vendors").insert(db_vendor).execute()
            vendor_id = res.data[0]["id"]
            logger.info(f"Vendor profile created with ID: {vendor_id}")
        except Exception as e:
            logger.error(f"Vendor profile creation failed: {str(e)}")
            # Try to clean up
            try:
                supabase.table("users").delete().eq("id", user_id).execute()
                supabase.auth.admin.delete_user(user_id)
            except:
                pass
            raise HTTPException(status_code=500, detail=f"Failed to create vendor profile: {str(e)}")
        
        # 4. Create Services
        try:
            services = data.get("services", [])
            logger.info(f"Creating {len(services)} services for vendor {vendor_id}")
            for s in services:
                db_service = {
                    "vendor_id": vendor_id,
                    "service_name": s.get("serviceName"),
                    "service_description": s.get("serviceDescription"),
                    "currency": s.get("currency"),
                    "retail_price": s.get("retailPrice"),
                    "commission": s.get("commission"),
                    "net_price": s.get("netPrice")
                }
                supabase.table("vendor_services").insert(db_service).execute()
            logger.info(f"All services created successfully")
        except Exception as e:
            logger.error(f"Service creation failed: {str(e)}")
            # Services are optional, so we don't fail the entire registration
            logger.warning("Continuing despite service creation failure")
            
        logger.info(f"Vendor registration completed successfully. Vendor ID: {vendor_id}")
        return {"success": True, "vendor_id": vendor_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vendor registration error: {str(e)}")
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
