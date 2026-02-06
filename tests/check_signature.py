import os
from dotenv import load_dotenv
from supabase import create_client
import inspect

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

print(f"Supabase Auth Class: {type(supabase.auth)}")
print(f"sign_up method signature: {inspect.signature(supabase.auth.sign_up)}")
