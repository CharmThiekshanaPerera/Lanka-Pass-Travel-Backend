# mongo_config.py
"""
MongoDB Atlas Configuration and Client Setup
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# MongoDB connection string from environment
MONGO_URI = os.getenv("MONGO_URI", "")


# Global client instance
_mongo_client: AsyncIOMotorClient = None
_database = None


async def get_mongo_client() -> AsyncIOMotorClient:
    """Get or create MongoDB client instance"""
    global _mongo_client
    
    if _mongo_client is None:
        if not MONGO_URI:
            logger.warning("MONGO_URI not configured - chat features will be unavailable")
            return None
        
        try:
            # Standard Atlas connection options for Windows/SSL issues
            options = {
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 5000,
                "retryWrites": True,
                "tls": True,
                "maxPoolSize": 50,
                "minPoolSize": 10
            }
            
            # Use certifi for CA certificates
            try:
                import certifi
                options["tlsCAFile"] = certifi.where()
                logger.info("Using certifi CA bundle for MongoDB connection")
            except ImportError:
                logger.warning("certifi not found, relying on system CA certificates")

            # Initialize client
            _mongo_client = AsyncIOMotorClient(MONGO_URI, **options)
            
            # Test connection with a short timeout
            await _mongo_client.admin.command('ping')
            logger.info("Successfully connected to MongoDB Atlas")
            return _mongo_client
            
        except Exception as e:
            logger.error(f"MongoDB connection attempt 1 failed: {str(e)}")
            
            # Second attempt: try allowing invalid certificates (common fallback for SSL issues)
            try:
                logger.warning("Retrying with tlsAllowInvalidCertificates=True")
                # Create a new options dict for retry
                retry_options = {
                    "serverSelectionTimeoutMS": 5000,
                    "connectTimeoutMS": 5000,
                    "tlsAllowInvalidCertificates": True,
                    "tls": True
                }
                _mongo_client = AsyncIOMotorClient(MONGO_URI, **retry_options)
                await _mongo_client.admin.command('ping')
                logger.info("Successfully connected to MongoDB Atlas (Insecure Mode)")
                return _mongo_client
            except Exception as e2:
                logger.error(f"MongoDB connection attempt 2 failed: {str(e2)}")
                _mongo_client = None
                return None
            
            _mongo_client = None
            
    return _mongo_client



async def get_database():
    """Get the MongoDB database instance"""
    global _database
    
    if _database is None:
        client = await get_mongo_client()
        if client is not None:
            _database = client.get_database("lankapass")
            
    return _database



async def get_chat_messages_collection():
    """Get the chat_messages collection"""
    db = await get_database()
    if db is not None:
        return db.get_collection("chat_messages")
    return None


async def get_update_requests_collection():
    """Get the update_requests collection"""
    db = await get_database()
    if db is not None:
        return db.get_collection("update_requests")
    return None


async def close_mongo_connection():
    """Close MongoDB connection on shutdown"""
    global _mongo_client, _database
    
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        _database = None
        logger.info("MongoDB connection closed")


# Ensure indexes are created
async def ensure_indexes():
    """Create necessary MongoDB indexes"""
    try:
        messages_col = await get_chat_messages_collection()
        if messages_col is not None:
            # Index for fetching vendor's messages
            await messages_col.create_index([("vendor_id", 1), ("created_at", 1)])
            # Index for unread count
            await messages_col.create_index([("sender", 1), ("read_at", 1)])
            logger.info("Chat message indexes ensured")
            
        requests_col = await get_update_requests_collection()
        if requests_col is not None:
            # Index for fetching vendor's requests
            await requests_col.create_index([("vendor_id", 1), ("status", 1)])
            await requests_col.create_index("created_at")
        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.error(f"Failed to create MongoDB indexes: {str(e)}")
