from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.schemas.vendor import VendorUpdate, VendorResponse, VendorStatus
from app.services.vendor_service import VendorService
from app.api.dependencies import get_current_active_user, require_vendor, require_admin

router = APIRouter(prefix="/vendor", tags=["Vendor"])

@router.get("/dashboard")
async def get_vendor_dashboard(
    current_user: dict = Depends(require_vendor)
) -> dict:
    """Get vendor dashboard data"""
    return await VendorService.get_vendor_dashboard(current_user["id"])

@router.get("/profile")
async def get_vendor_profile(
    current_user: dict = Depends(require_vendor)
) -> dict:
    """Get vendor profile"""
    vendor = await VendorService.get_vendor_by_user_id(current_user["id"])
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor profile not found"
        )
    return vendor

@router.put("/profile")
async def update_vendor_profile(
    vendor_data: VendorUpdate,
    current_user: dict = Depends(require_vendor)
) -> dict:
    """Update vendor profile"""
    vendor = await VendorService.get_vendor_by_user_id(current_user["id"])
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor profile not found"
        )
    
    return await VendorService.update_vendor(vendor["id"], vendor_data)

@router.get("/all", dependencies=[Depends(require_admin)])
async def get_all_vendors(
    status: Optional[VendorStatus] = None
) -> List[VendorResponse]:
    """Get all vendors (admin only)"""
    return await VendorService.get_all_vendors(status)

@router.patch("/{vendor_id}/status", dependencies=[Depends(require_admin)])
async def update_vendor_status(
    vendor_id: str,
    status: VendorStatus
) -> dict:
    """Update vendor status (admin only)"""
    return await VendorService.update_vendor_status(vendor_id, status)