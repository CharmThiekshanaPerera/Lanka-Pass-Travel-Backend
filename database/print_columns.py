import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

for table in ["vendors", "vendor_services"]:
    res = supabase.table(table).select("*").limit(1).execute()
    if res.data:
        print(f"--- {table} ---")
        cols = sorted(list(res.data[0].keys()))
        for col in cols:
            print(col)
    else:
        print(f"--- {table} (EMPTY) ---")
