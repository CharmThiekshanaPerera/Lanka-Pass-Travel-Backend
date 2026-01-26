from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from app.database.supabase_client import SupabaseManager
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorStatus
import logging

logger = logging.getLogger(__name__)

class VendorService:
    
    @staticmethod
    async def get_vendor_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get vendor by user ID"""
        result = await SupabaseManager.execute_query(
            table="vendors",
            operation="select",
            filters={"user_id": user_id},
            single=True
        )
        
        return result["data"] if result["success"] else None
    
    @staticmethod
    async def create_vendor(vendor_data: VendorCreate) -> Dict[str, Any]:
        """Create a new vendor"""
        result = await SupabaseManager.execute_query(
            table="vendors",
            operation="insert",
            data=vendor_data.dict()
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create vendor"
            )
        
        return result["data"][0] if result["data"] else {}
    
    @staticmethod
    async def update_vendor(vendor_id: str, vendor_data: VendorUpdate) -> Dict[str, Any]:
        """Update vendor"""
        result = await SupabaseManager.execute_query(
            table="vendors",
            operation="update",
            data=vendor_data.dict(exclude_unset=True),
            filters={"id": vendor_id}
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update vendor"
            )
        
        return result["data"][0] if result["data"] else {}
    
    @staticmethod
    async def get_vendor_dashboard(user_id: str) -> Dict[str, Any]:
        """Get vendor dashboard data"""
        # Get vendor profile
        vendor = await VendorService.get_vendor_by_user_id(user_id)
        
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor profile not found"
            )
        
        # Get vendor statistics (customize based on your business logic)
        stats_result = await SupabaseManager.execute_query(
            table="bookings",
            operation="select",
            filters={"vendor_id": vendor["id"]}
        )
        
        bookings = stats_result["data"] if stats_result["success"] else []
        
        # Calculate statistics
        total_bookings = len(bookings)
        pending_bookings = len([b for b in bookings if b.get("status") == "pending"])
        completed_bookings = len([b for b in bookings if b.get("status") == "completed"])
        
        # Calculate revenue (assuming booking has amount field)
        total_revenue = sum([b.get("amount", 0) for b in bookings if b.get("status") == "completed"])
        
        return {
            "vendor": vendor,
            "stats": {
                "total_bookings": total_bookings,
                "pending_bookings": pending_bookings,
                "completed_bookings": completed_bookings,
                "total_revenue": total_revenue
            },
            "recent_bookings": bookings[:10]  # Last 10 bookings
        }
    
    @staticmethod
    async def get_all_vendors(status: Optional[VendorStatus] = None) -> List[Dict[str, Any]]:
        """Get all vendors (for admin)"""
        filters = {}
        if status:
            filters["status"] = status
        
        result = await SupabaseManager.execute_query(
            table="vendors",
            operation="select",
            filters=filters
        )
        
        if not result["success"]:
            return []
        
        vendors = result["data"] or []
        
        # Get user details for each vendor
        for vendor in vendors:
            user_result = await SupabaseManager.execute_query(
                table="users",
                operation="select",
                filters={"id": vendor["user_id"]},
                single=True
            )
            
            if user_result["success"] and user_result["data"]:
                vendor["user"] = {
                    "email": user_result["data"]["email"],
                    "name": user_result["data"]["name"],
                    "role": user_result["data"]["role"]
                }
        
        return vendors
    
    @staticmethod
    async def update_vendor_status(vendor_id: str, status: VendorStatus) -> Dict[str, Any]:
        """Update vendor status (admin only)"""
        result = await SupabaseManager.execute_query(
            table="vendors",
            operation="update",
            data={"status": status},
            filters={"id": vendor_id}
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update vendor status"
            )
        
        return result["data"][0] if result["data"] else {}