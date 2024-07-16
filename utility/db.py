import psycopg2
import os
from supabase import create_client


def create_supabase_client():
    url: str = os.getenv("SUPABASE_URL")
    key: str = os.getenv("SUPABASE_KEY")
    return create_client(url, key)


def instantiate_db_connection():
    """Returns the connection from the DB"""

    db_uri = os.getenv("DB_URI")
    return psycopg2.connect(db_uri)


def delete_all_opportunity_type(opp_type: str) -> None:
    """Deletes all opportunities of a specific type for testing purposes only"""
    supabase = create_supabase_client()
    supabase.table("opportunities_table").delete().eq("type", opp_type).execute()


def reset_processed_status(TABLE_NAME: str) -> None:
    """Jobs status will be set to _processed = 0 for testing a debugging purposes"""

    supabase = create_supabase_client()
    supabase.table(TABLE_NAME).update({"processed": 0}).eq("processed", 1).limit(5)
