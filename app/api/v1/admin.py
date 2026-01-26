from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.database.supabase_client import SupabaseManager
from app.api.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/dashboard")
async def get_admin_dashboard(
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """Get admin dashboard data"""
    
    # Get user statistics
    users_result = await SupabaseManager.execute_query(
        table="users",
        operation="select"
    )
    
    # Get vendor statistics
    vendors_result = await SupabaseManager.execute_query(
        table="vendors",
        operation="select"
    )
    
    # Get booking statistics
    bookings_result = await SupabaseManager.execute_query(
        table="bookings",
        operation="select"
    )
    
    users = users_result["data"] or []
    vendors = vendors_result["data"] or []
    bookings = bookings_result["data"] or []
    
    # Calculate statistics
    total_users = len(users)
    total_vendors = len(vendors)
    total_bookings = len(bookings)
    
    # Group vendors by status
    vendors_by_status = {}
    for vendor in vendors:
        status = vendor.get("status", "pending")
        vendors_by_status[status] = vendors_by_status.get(status, 0) + 1
    
    # Group users by role
    users_by_role = {}
    for user in users:
        role = user.get("role", "user")
        users_by_role[role] = users_by_role.get(role, 0) + 1
    
    return {
        "stats": {
            "total_users": total_users,
            "total_vendors": total_vendors,
            "total_bookings": total_bookings,
            "vendors_by_status": vendors_by_status,
            "users_by_role": users_by_role
        },
        "recent_users": users[:10],
        "recent_vendors": vendors[:10],
        "recent_bookings": bookings[:10]
    }