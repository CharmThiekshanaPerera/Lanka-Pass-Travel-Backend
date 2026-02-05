import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def check_columns(table_name):
    try:
        # Fetch one row to see columns or use RPC if available
        # But standard way to see columns is querying information_schema
        res = supabase.rpc("get_columns", {"table_name": table_name}).execute()
        if res.data:
            print(f"\nColumns for {table_name}:")
            for col in res.data:
                print(f"- {col}")
        else:
            # Fallback: select one record
            res = supabase.table(table_name).select("*").limit(1).execute()
            if res.data:
                print(f"\nColumns for {table_name} (from data):")
                for key in res.data[0].keys():
                    print(f"- {key}")
            else:
                print(f"No data in {table_name} to check columns via select *.")
    except Exception as e:
        print(f"Error checking columns for {table_name}: {e}")

# Since RPC get_columns might not exist, I'll try to use the query
try:
    # A common trick to get columns via REST API is to use ?select=* on an empty result
    # but PostgREST doesn't return column names in headers usually.
    # I'll just try to select everything and see the keys of the first object.
    for table in ["vendors", "vendor_services"]:
        res = supabase.table(table).select("*").limit(1).execute()
        if res.data:
            print(f"\nTable: {table}")
            for col in res.data[0].keys():
                print(f"- {col}")
        else:
            print(f"\nTable: {table} is empty. Trying to find columns another way...")
except Exception as e:
    print(f"Error: {e}")
