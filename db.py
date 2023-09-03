import psycopg2
import os


def instantiate_db_connection():
    """Returns the connection from the DB"""

    db_uri = os.getenv("DB_URI")
    return psycopg2.connect(db_uri)


def add_column(column_name: str, data_type: str) -> None:
    """Adds a column for adjustment to the table after the table has been created"""

    with instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(f"ALTER TABLE jobs_table ADD COLUMN {column_name} {data_type}")

        connection.commit()


def delete_alL_opportunity_type(opp_type: str) -> None:
    """Deletes all opportunities of a specific type for testing purposes only"""

    with instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("DELETE FROM jobs_table WHERE type = %s", (opp_type,))
        connection.commit()
