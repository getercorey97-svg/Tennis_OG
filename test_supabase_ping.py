import os
from supabase import create_client, Client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("ERROR: Supabase environment variables missing!")
    exit(1)

supabase: Client = create_client(url, key)
try:
    res = supabase.table("ping_table").insert({"ping": True}).execute()
    print("SUCCESS: Keep-alive ping successfully written to Supabase ping_table.")
except Exception as e:
    print(f"ERROR: Failed to write ping: {e}")
