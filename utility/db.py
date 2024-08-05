import os
from supabase import create_client
from dataclasses import dataclass
from dotenv import load_dotenv
import requests
from utility.error import ErrorMsg

load_dotenv()
ERROR_MSG = ErrorMsg()


@dataclass
class SupabaseConnection:
    """Constructs Supabase connection."""

    CLIENT: any = None
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    SUPABASE_API_URL: str = f"{SUPABASE_URL}/rest/v1/rpc"

    def __post_init__(self):
        self.CLIENT = self.create_supabase_client()

    def create_supabase_client(self):
        """Creates the Supabase client with the URL and key variables."""

        return create_client(self.SUPABASE_URL, self.SUPABASE_KEY)


SUPABASE_INSTANCE = SupabaseConnection().CLIENT


def delete_all_opportunity_type(TABLE_NAME: str, opp_type: str) -> None:
    """Deletes all opportunities of a specific type for testing purposes only."""

    SUPABASE_INSTANCE.table(TABLE_NAME).delete().eq("type", opp_type).execute()


def reset_processed_status(TABLE_NAME: str) -> None:
    """Jobs status will be set to _processed = 0 for testing a debugging purposes"""

    SUPABASE_INSTANCE.table(TABLE_NAME).update({"processed": 0}).eq(
        "processed", 1
    ).limit(5).execute()


def execute_sql(sql: str):
    """Executes a raw SQL query using the Supabase HTTP API."""
    connection = SupabaseConnection()
    headers = {
        "apikey": connection.SUPABASE_KEY,
        "Authorization": f"Bearer {connection.SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    data = {"query": sql}
    response = requests.post(connection.SUPABASE_API_URL, headers=headers, json=data)

    response.raise_for_status()
    return response


def create_table(TABLE_NAME: str) -> None:
    """Creates a new table in Supabase database. Only needs to be called once."""

    request = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        company TEXT,
        title TEXT,
        link TEXT,
        processed INTEGER DEFAULT 0,
        type TEXT
    );
    """

    response = execute_sql(request)

    if response.status_code != 200:
        return ERROR_MSG.status_code_failure(response.status_code)

    return "Request executed successfully."


def add_column(column_name: str, data_type: str) -> None:
    """Adds a column for adjustment to the table after the table has been created"""

    TABLE_NAME = os.getenv("DB_TABLE")

    request = f"""
        ALTER TABLE {TABLE_NAME} ADD COLUMN {column_name} {data_type};
    """

    response = execute_sql(request)

    if response.status_code != 200:
        return ERROR_MSG.status_code_failure(response.status_code)

    return "Request executed successfully."
