import os
from typing import Optional, Dict, Any
from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class SupabaseManager:
    _instance: Optional[Client] = None
    _admin_instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Singleton pattern for Supabase client"""
        if cls._instance is None:
            try:
                cls._instance = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                logger.info("✅ Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Supabase client: {e}")
                raise
        return cls._instance
    
    @classmethod
    def get_admin_client(cls) -> Client:
        """Returns a fixed Supabase client for admin operations to avoid session pollution.
        This instance should NEVER be used for supabase.auth.sign_in() operations.
        """
        if cls._admin_instance is None:
            try:
                cls._admin_instance = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                logger.info("✅ Supabase ADMIN client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Supabase admin client: {e}")
                raise
        return cls._admin_instance
    
    @classmethod
    async def execute_query(cls, table: str, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute a query on Supabase"""
        client = cls.get_client()
        
        try:
            table_ref = client.table(table)
            
            if operation == "select":
                query = table_ref.select("*")
                if "filters" in kwargs:
                    for filter_key, filter_value in kwargs["filters"].items():
                        query = query.eq(filter_key, filter_value)
                if "single" in kwargs and kwargs["single"]:
                    response = query.single().execute()
                else:
                    response = query.execute()
            
            elif operation == "insert":
                data = kwargs.get("data", {})
                response = table_ref.insert(data).execute()
            
            elif operation == "update":
                data = kwargs.get("data", {})
                filters = kwargs.get("filters", {})
                query = table_ref.update(data)
                for filter_key, filter_value in filters.items():
                    query = query.eq(filter_key, filter_value)
                response = query.execute()
            
            elif operation == "delete":
                filters = kwargs.get("filters", {})
                query = table_ref.delete()
                for filter_key, filter_value in filters.items():
                    query = query.eq(filter_key, filter_value)
                response = query.execute()
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            return {
                "success": True,
                "data": response.data if hasattr(response, 'data') else None,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Supabase query error: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }
    
    @classmethod
    async def auth(cls):
        """Get auth client"""
        return cls.get_client().auth

# Initialize supabase client
supabase = SupabaseManager.get_client()