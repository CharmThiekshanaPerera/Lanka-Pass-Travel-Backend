import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def find_all_data():
    mongo_uri = os.getenv("MONGO_URI")
    client = AsyncIOMotorClient(mongo_uri)
    
    try:
        dbs = await client.list_database_names()
        print(f"Databases: {dbs}")
        for db_name in dbs:
            if db_name in ['admin', 'local', 'config']: continue
            db = client[db_name]
            cols = await db.list_collection_names()
            print(f"  DB: {db_name} | Collections: {cols}")
            for col_name in cols:
                count = await db[col_name].count_documents({})
                print(f"    Col: {col_name} | Count: {count}")
                if count > 0:
                    latest = await db[col_name].find().sort("_id", -1).limit(1).to_list(1)
                    print(f"      Latest doc: {latest[0]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(find_all_data())
