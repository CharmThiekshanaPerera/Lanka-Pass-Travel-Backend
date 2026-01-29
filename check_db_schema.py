
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

def check_table_columns(table_name):
    print(f"\n--- Checking columns for table: {table_name} ---")
    try:
        # Get one row to see columns
        res = supabase.table(table_name).select("*").limit(1).execute()
        if res.data:
            columns = sorted(list(res.data[0].keys()))
            print(f"Total columns: {len(columns)}")
            for col in columns:
                print(f" - {col}")
        else:
            print(f"Table {table_name} is empty, attempting to get columns via RPC if available or insert/rollback...")
            # If empty, we can't easily see columns with just select("*") in some libraries
            # but supabase-py usually handles it if the table exists.
            print(f"Table {table_name} seems empty of rows.")
    except Exception as e:
        print(f"Error checking {table_name}: {e}")

check_table_columns("vendors")
check_table_columns("vendor_services")
check_table_columns("users")
