from supabase import create_client, Client
from app.config import settings


def get_supabase_client() -> Client:
    """
    Factory function that creates the Supabase client using config values.
    Injected via FastAPI Depends — never imported as a global in other modules.
    """
    return create_client(settings.supabase_url, settings.supabase_key)
