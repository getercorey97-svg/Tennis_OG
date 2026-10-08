import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://eqhrzpfvwihchhlmutxr.supabase.co")
SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVxaHJ6cGZ2d2loY2hobG11dHhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE0MzgzODEsImV4cCI6MjEwNzAxNDM4MX0.PvwTapSgpKxbWnVslzAQpnFDXFnuraS_csZPE6_CK_E"
)

def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("CRITICAL: Supabase credentials are missing or unset.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_connection() -> bool:
    client = get_supabase_client()
    try:
        response = client.table("ping_table").insert({
            "caller": "tennis-og-terminal-handshake"
        }).execute()
        return len(response.data) > 0
    except Exception as e:
        sys.stderr.write(f"Database connection verification failed: {str(e)}\n")
        return False

def batch_upsert(table_name: str, records: List[Dict[str, Any]], chunk_size: int = 500) -> int:
    if not records:
        return 0
    client = get_supabase_client()
    total_committed = 0
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        try:
            response = client.table(table_name).upsert(chunk).execute()
            total_committed += len(response.data)
        except Exception as e:
            sys.stderr.write(f"Failed to upsert chunk into {table_name}: {str(e)}\n")
            raise e
    return total_committed

if __name__ == "__main__":
    print("Testing Supabase connectivity...")
    if verify_connection():
        print("SUCCESS: Supabase connected and operational.")
    else:
        print("FAILURE: Handshake failed. Ensure table schemas are executed in Supabase SQL editor.")
