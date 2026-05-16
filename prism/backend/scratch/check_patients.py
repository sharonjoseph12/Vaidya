
from backend.db.supabase_client import get_supabase_client
client = get_supabase_client()
res = client.table("patients").select("id").execute()
print(f"Patients: {res.data}")
