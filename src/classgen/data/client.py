"""Supabase client initialization for ClassGen data layer.

Handles client creation with PostgREST URL fix for self-hosted instances.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

# --- Client init ---

supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_KEY", "")
supabase: Client | None = None
if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
        # supabase-py appends /rest/v1/ but raw PostgREST serves at root —
        # replace the internal postgrest client with one at the correct URL
        from postgrest import SyncPostgrestClient

        supabase._postgrest = SyncPostgrestClient(
            base_url=supabase_url,
            headers={"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"},
        )
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")
