# chat_service.py
"""
Chat and Update Request Service Layer
Handles all chat messages and vendor update approval workflows
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
import logging
import asyncio

from app.database.mongo_config import (
    get_chat_messages_collection,
    get_update_requests_collection
)
from app.database.supabase_client import SupabaseManager


logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat messages and update requests"""
    
    # ==================== CHAT MESSAGES ====================
    
    async def create_message(
        self,
        vendor_id: str,
        sender: str,  # "vendor" or "admin"
        sender_id: str,
        sender_name: str,
        message: str,
        message_type: str = "text",  # "text", "update_request", "system"
        attachments: Optional[List[Dict]] = None,
        update_request_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Create a new chat message"""
        try:
            collection = await get_chat_messages_collection()
            if collection is None:
                logger.error("MongoDB not available - cannot create message")
                return None
            
            doc = {
                "vendor_id": vendor_id,
                "sender": sender,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "message": message,
                "message_type": message_type,
                "attachments": attachments or [],
                "update_request_id": update_request_id,
                "created_at": datetime.utcnow(),
                "read_at": None
            }
            
            result = await collection.insert_one(doc)
            doc["_id"] = str(result.inserted_id)
            
            logger.info(f"Chat message created: {result.inserted_id}")
            return self._serialize_message(doc)
            
        except Exception as e:
            logger.error(f"Error creating chat message: {str(e)}")
            return None



    
    async def get_messages_by_vendor(
        self,
        vendor_id: str,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict]:
        """Get chat messages for a specific vendor"""
        try:
            collection = await get_chat_messages_collection()


            if collection is None:
                return []

            
            cursor = collection.find(
                {"vendor_id": vendor_id}
            ).sort("created_at", 1).skip(skip).limit(limit)
            
            messages = []
            async for doc in cursor:
                messages.append(self._serialize_message(doc))
            
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}")
            return []
    
    async def get_all_admin_messages(
        self,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict]:
        """Get all messages for admin view (grouped by vendor)"""
        try:
            collection = await get_chat_messages_collection()
            if collection is None:
                return []
            
            # Get recent messages
            cursor = collection.find().sort("created_at", -1).skip(skip).limit(limit)
            
            messages = []
            async for doc in cursor:
                messages.append(self._serialize_message(doc))
            
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching admin messages: {str(e)}")
            return []
    
    async def mark_messages_read(
        self,
        vendor_id: str,
        reader: str  # "vendor" or "admin"
    ) -> bool:
        """Mark messages as read"""
        try:
            collection = await get_chat_messages_collection()
            if collection is None:
                return False
            
            # Mark messages from the other party as read
            sender_filter = "admin" if reader == "vendor" else "vendor"
            
            await collection.update_many(
                {
                    "vendor_id": vendor_id,
                    "sender": sender_filter,
                    "read_at": None
                },
                {"$set": {"read_at": datetime.utcnow()}}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking messages read: {str(e)}")
            return False
    
    async def get_unread_count_for_admin(self) -> int:
        """Get count of unread messages from vendors"""
        try:
            collection = await get_chat_messages_collection()
            if collection is None:
                return 0
            
            count = await collection.count_documents({
                "sender": "vendor",
                "read_at": None
            })
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0

    async def get_unread_count_for_vendor(self, vendor_id: str) -> int:
        """Get count of unread messages from admin for a specific vendor"""
        try:
            collection = await get_chat_messages_collection()
            if collection is None:
                return 0
            
            count = await collection.count_documents({
                "vendor_id": vendor_id,
                "sender": "admin",
                "read_at": None
            })
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting vendor unread count: {str(e)}")
            return 0

    async def get_admin_chat_summary(self) -> List[Dict]:
        """Get summary of chats for admin (latest message and unread count per vendor)"""
        try:
            collection = await get_chat_messages_collection()
            if collection is None:
                return []
            
            # Aggregate to find latest message and unread count per vendor
            pipeline = [
                {"$match": {"vendor_id": {"$ne": None}}}, # Filter out rogue messages without vendor_id
                {"$sort": {"created_at": -1}}, # Sort messages by date descending
                {
                    "$group": {
                        "_id": "$vendor_id",
                        "latest_message": {"$first": "$$ROOT"},
                        "unread_count": {
                            "$sum": {
                                "$cond": [
                                    {"$and": [
                                        {"$eq": ["$sender", "vendor"]},
                                        {"$eq": ["$read_at", None]}
                                    ]},
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                },
                {"$sort": {"latest_message.created_at": -1}} # Sort vendors by latest message
            ]
            
            cursor = collection.aggregate(pipeline)
            temp_summary = []
            vendor_ids = []
            
            async for doc in cursor:
                vendor_id = doc["_id"]
                latest_msg = self._serialize_message(doc["latest_message"])
                unread_count = doc["unread_count"]
                
                temp_summary.append({
                    "vendor_id": vendor_id,
                    "latest_message": latest_msg,
                    "unread_count": unread_count
                })
                vendor_ids.append(vendor_id)

            # Bulk fetch vendor names from Supabase
            vendor_names = {}
            if vendor_ids:
                try:
                    from app.database.supabase_client import supabase_admin
                    # Use asyncio.to_thread for the bulk query
                    vendor_res = await asyncio.to_thread(
                        supabase_admin.table("vendors")
                        .select("id, business_name")
                        .in_("id", vendor_ids)
                        .execute
                    )
                    if vendor_res.data:
                        vendor_names = {v["id"]: v["business_name"] for v in vendor_res.data}
                except Exception as e:
                    logger.error(f"Error fetching vendor names bulk: {str(e)}")

            summary = []
            for item in temp_summary:
                item["vendor_name"] = vendor_names.get(item["vendor_id"], "Unknown Vendor")
                summary.append(item)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting admin chat summary: {str(e)}")
            return []
    
    # ==================== UPDATE REQUESTS ====================
    
    async def create_update_request(
        self,
        vendor_id: str,
        requested_by: str,
        requested_by_name: str,
        current_data: Dict[str, Any],
        requested_data: Dict[str, Any],
        changed_fields: List[str]
    ) -> Optional[Dict]:
        """Create a new vendor profile update request"""
        try:
            collection = await get_update_requests_collection()
            if collection is None:
                logger.error("MongoDB not available - cannot create update request")
                return None
            
            doc = {
                "vendor_id": vendor_id,
                "requested_by": requested_by,
                "requested_by_name": requested_by_name,
                "request_type": "profile_update",
                "current_data": current_data,
                "requested_data": requested_data,
                "changed_fields": changed_fields,
                "status": "pending",
                "reviewed_by": None,
                "reviewed_by_name": None,
                "review_reason": None,
                "created_at": datetime.utcnow(),
                "reviewed_at": None
            }
            
            result = await collection.insert_one(doc)
            doc["_id"] = str(result.inserted_id)
            
            logger.info(f"Update request created: {result.inserted_id}")
            
            # Create a chat message about this update request
            field_summary = ", ".join(changed_fields[:5])
            if len(changed_fields) > 5:
                field_summary += f" and {len(changed_fields) - 5} more"
            
            await self.create_message(
                vendor_id=vendor_id,
                sender="vendor",
                sender_id=requested_by,
                sender_name=requested_by_name,
                message=f"📝 Profile update request submitted.\n\nFields to update: {field_summary}\n\nPlease review and approve the changes.",
                message_type="update_request",
                update_request_id=str(result.inserted_id)
            )
            
            return self._serialize_update_request(doc)
            
        except Exception as e:
            logger.error(f"Error creating update request: {str(e)}")
            return None
    
    async def create_service_update_request(
        self,
        vendor_id: str,
        service_id: str,
        requested_by: str,
        requested_by_name: str,
        current_data: Dict[str, Any],
        requested_data: Dict[str, Any],
        changed_fields: List[str]
    ) -> Optional[Dict]:
        """Create a new service update request"""
        try:
            collection = await get_update_requests_collection()
            if collection is None:
                logger.error("MongoDB not available - cannot create service update request")
                return None
            
            doc = {
                "vendor_id": vendor_id,
                "service_id": service_id,  # NEW: track which service
                "requested_by": requested_by,
                "requested_by_name": requested_by_name,
                "request_type": "service_update",  # NEW: distinguish from profile updates
                "current_data": current_data,
                "requested_data": requested_data,
                "changed_fields": changed_fields,
                "status": "pending",
                "reviewed_by": None,
                "reviewed_by_name": None,
                "review_reason": None,
                "created_at": datetime.utcnow(),
                "reviewed_at": None
            }
            
            result = await collection.insert_one(doc)
            doc["_id"] = str(result.inserted_id)
            
            logger.info(f"Service update request created: {result.inserted_id}")
            
            # Create a chat message about this update request
            field_summary = ", ".join(changed_fields[:5])
            if len(changed_fields) > 5:
                field_summary += f" and {len(changed_fields) - 5} more"
            
            await self.create_message(
                vendor_id=vendor_id,
                sender="vendor",
                sender_id=requested_by,
                sender_name=requested_by_name,
                message=f"📝 Service update request submitted.\n\nFields to update: {field_summary}\n\nPlease review and approve the changes.",
                message_type="update_request",
                update_request_id=str(result.inserted_id)
            )
            
            return self._serialize_update_request(doc)
            
        except Exception as e:
            logger.error(f"Error creating service update request: {str(e)}")
            return None
    
    async def create_service_addition_request(
        self,
        vendor_id: str,
        requested_by: str,
        requested_by_name: str,
        requested_data: Dict[str, Any]
    ) -> Optional[Dict]:
        """Create a new service addition request"""
        try:
            collection = await get_update_requests_collection()
            if collection is None:
                logger.error("MongoDB not available - cannot create service addition request")
                return None
            
            doc = {
                "vendor_id": vendor_id,
                "requested_by": requested_by,
                "requested_by_name": requested_by_name,
                "request_type": "service_addition",
                "current_data": {}, # Empty for new additions
                "requested_data": requested_data,
                "changed_fields": list(requested_data.keys()),
                "status": "pending",
                "reviewed_by": None,
                "reviewed_by_name": None,
                "review_reason": None,
                "created_at": datetime.utcnow(),
                "reviewed_at": None
            }
            
            result = await collection.insert_one(doc)
            doc["_id"] = str(result.inserted_id)
            
            logger.info(f"Service addition request created: {result.inserted_id}")
            
            # Create a chat message about this request
            service_name = requested_data.get("service_name", "New Service")
            await self.create_message(
                vendor_id=vendor_id,
                sender="vendor",
                sender_id=requested_by,
                sender_name=requested_by_name,
                message=f"🆕 New service addition request: **{service_name}**.\n\nPlease review and approve the new service.",
                message_type="update_request",
                update_request_id=str(result.inserted_id)
            )
            
            return self._serialize_update_request(doc)
            
        except Exception as e:
            logger.error(f"Error creating service addition request: {str(e)}")
            return None
    
    async def get_pending_update_requests(
        self,
        vendor_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict]:
        """Get pending update requests"""
        try:
            collection = await get_update_requests_collection()
            if collection is None:
                return []
            
            query = {"status": "pending"}
            if vendor_id:
                query["vendor_id"] = vendor_id
            
            cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            
            requests = []
            async for doc in cursor:
                requests.append(self._serialize_update_request(doc))
            
            return requests
            
        except Exception as e:
            logger.error(f"Error fetching update requests: {str(e)}")
            return []
    
    async def get_update_request_by_id(self, request_id: str) -> Optional[Dict]:
        """Get a specific update request by ID"""
        try:
            collection = await get_update_requests_collection()
            if collection is None:
                return None
        
            
            doc = await collection.find_one({"_id": ObjectId(request_id)})
            if doc:
                return self._serialize_update_request(doc)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching update request: {str(e)}")
            return None
    
    async def approve_update_request(
        self,
        request_id: str,
        reviewed_by: str,
        reviewed_by_name: str
    ) -> Optional[Dict]:
        """Approve an update request (profile or service)"""
        try:
            collection = await get_update_requests_collection()
            if collection is None:
                return None
            
            # Update the request status
            result = await collection.find_one_and_update(
                {"_id": ObjectId(request_id), "status": "pending"},
                {
                    "$set": {
                        "status": "approved",
                        "reviewed_by": reviewed_by,
                        "reviewed_by_name": reviewed_by_name,
                        "reviewed_at": datetime.utcnow()
                    }
                },
                return_document=True
            )
            
            if result:
                request_type = result.get("request_type", "profile_update")
                vendor_id = result["vendor_id"]
                requested_data = result["requested_data"]
                
                # Handle based on request type
                if request_type == "service_update":
                    # Apply changes to vendor_services table
                    service_id = result.get("service_id")
                    if service_id and requested_data:
                        db_res = await SupabaseManager.execute_query(
                            table="vendor_services",
                            operation="update",
                            data=requested_data,
                            filters={"id": service_id}
                        )
                        
                        if not db_res["success"]:
                            logger.error(f"Failed to update service: {db_res['error']}")
                    
                    # Create a system message about approval
                    await self.create_message(
                        vendor_id=vendor_id,
                        sender="admin",
                        sender_id=reviewed_by,
                        sender_name=reviewed_by_name,
                        message=f"✅ Your service update request has been **approved** by {reviewed_by_name}.\n\nYour service has been updated successfully.",
                        message_type="system",
                        update_request_id=request_id
                    )
                elif request_type == "service_addition":
                    # Apply changes to vendor_services table (INSERT)
                    if requested_data:
                        # Ensure vendor_id is in the data
                        requested_data["vendor_id"] = vendor_id
                        db_res = await SupabaseManager.execute_query(
                            table="vendor_services",
                            operation="insert",
                            data=requested_data
                        )
                        
                        if not db_res["success"]:
                            logger.error(f"Failed to add new service: {db_res['error']}")
                    
                    # Create a system message about approval
                    service_name = requested_data.get("service_name", "New Service")
                    await self.create_message(
                        vendor_id=vendor_id,
                        sender="admin",
                        sender_id=reviewed_by,
                        sender_name=reviewed_by_name,
                        message=f"✅ Your new service '**{service_name}**' has been **approved** by {reviewed_by_name}.\n\nThe service is now active.",
                        message_type="system",
                        update_request_id=request_id
                    )
                else:
                    # Profile update - use existing field mapping
                    FIELD_MAPPING = {
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
                        "tourismLicenseUrl": "tourism_license_url",
                        "logoUrl": "logo_url",
                        "coverImageUrl": "cover_image_url",
                        "galleryUrls": "gallery_urls"
                    }
                    
                    # Transform data to snake_case for DB
                    db_data = {}
                    for key, value in requested_data.items():
                        if key in FIELD_MAPPING:
                            db_data[FIELD_MAPPING[key]] = value
                        else:
                            db_data[key] = value # Fallback
                    
                    if db_data:
                        db_res = await SupabaseManager.execute_query(
                            table="vendors",
                            operation="update",
                            data=db_data,
                            filters={"id": vendor_id}
                        )
                        
                        if not db_res["success"]:
                            logger.error(f"Failed to update Supabase vendor profile: {db_res['error']}")
                    
                    # Create a system message about approval
                    await self.create_message(
                        vendor_id=vendor_id,
                        sender="admin",
                        sender_id=reviewed_by,
                        sender_name=reviewed_by_name,
                        message=f"✅ Your profile update request has been **approved** by {reviewed_by_name}.\n\nYour profile has been updated successfully.",
                        message_type="system",
                        update_request_id=request_id
                    )
                
                return self._serialize_update_request(result)

            
            return None
            
        except Exception as e:
            logger.error(f"Error approving update request: {str(e)}")
            return None
    
    async def reject_update_request(
        self,
        request_id: str,
        reviewed_by: str,
        reviewed_by_name: str,
        reason: str
    ) -> Optional[Dict]:
        """Reject an update request"""
        try:
            collection = await get_update_requests_collection()
            if collection is None:
                return None
        
            
            # Update the request status
            result = await collection.find_one_and_update(
                {"_id": ObjectId(request_id), "status": "pending"},
                {
                    "$set": {
                        "status": "rejected",
                        "reviewed_by": reviewed_by,
                        "reviewed_by_name": reviewed_by_name,
                        "review_reason": reason,
                        "reviewed_at": datetime.utcnow()
                    }
                },
                return_document=True
            )
            
            if result:
                # Create a system message about rejection
                await self.create_message(
                    vendor_id=result["vendor_id"],
                    sender="admin",
                    sender_id=reviewed_by,
                    sender_name=reviewed_by_name,
                    message=f"❌ Your profile update request has been **rejected** by {reviewed_by_name}.\n\n**Reason:** {reason}\n\nPlease review and resubmit if needed.",
                    message_type="system",
                    update_request_id=request_id
                )
                
                return self._serialize_update_request(result)
            
            return None
            
        except Exception as e:
            logger.error(f"Error rejecting update request: {str(e)}")
            return None
    
    async def get_all_update_requests(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict]:
        """Get all update requests (admin view)"""
        try:
            collection = await get_update_requests_collection()
            if collection is None:
                return []
            
            query = {}
            if status:
                query["status"] = status
            
            cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            
            requests = []
            async for doc in cursor:
                requests.append(self._serialize_update_request(doc))
            
            return requests
            
        except Exception as e:
            logger.error(f"Error fetching all update requests: {str(e)}")
            return []
    
    # ==================== HELPERS ====================
    
    def _serialize_message(self, doc: Dict) -> Dict:
        """Convert MongoDB document to JSON-serializable dict"""
        return {
            "id": str(doc.get("_id", "")),
            "vendor_id": doc.get("vendor_id"),
            "sender": doc.get("sender"),
            "sender_id": doc.get("sender_id"),
            "sender_name": doc.get("sender_name"),
            "message": doc.get("message"),
            "message_type": doc.get("message_type", "text"),
            "attachments": doc.get("attachments", []),
            "update_request_id": doc.get("update_request_id"),
            "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
            "read_at": doc.get("read_at").isoformat() if doc.get("read_at") else None
        }
    
    def _serialize_update_request(self, doc: Dict) -> Dict:
        """Convert MongoDB document to JSON-serializable dict"""
        return {
            "id": str(doc.get("_id", "")),
            "vendor_id": doc.get("vendor_id"),
            "service_id": doc.get("service_id"),  # NEW: for service updates
            "requested_by": doc.get("requested_by"),
            "requested_by_name": doc.get("requested_by_name"),
            "request_type": doc.get("request_type"),
            "current_data": doc.get("current_data", {}),
            "requested_data": doc.get("requested_data", {}),
            "changed_fields": doc.get("changed_fields", []),
            "status": doc.get("status"),
            "reviewed_by": doc.get("reviewed_by"),
            "reviewed_by_name": doc.get("reviewed_by_name"),
            "review_reason": doc.get("review_reason"),
            "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
            "reviewed_at": doc.get("reviewed_at").isoformat() if doc.get("reviewed_at") else None
        }


# Singleton instance
chat_service = ChatService()
