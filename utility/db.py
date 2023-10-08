import psycopg2
import os


def instantiate_db_connection():
    """Returns the connection from the DB"""

    db_uri = os.getenv("DB_URI")
    return psycopg2.connect(db_uri)


def create(TABLE_NAME: str) -> None:
    """Creates the DB. Only needs to be called once."""

    with instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME}(company TEXT, title TEXT, location TEXT, link TEXT, processed INTEGER DEFAULT 0)"""
        )

        connection.commit()


def add_column(column_name: str, data_type: str) -> None:
    """Adds a column for adjustment to the table after the table has been created"""

    with instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(f"ALTER TABLE jobs_table ADD COLUMN {column_name} {data_type}")

        connection.commit()


def delete_all_opportunity_type(opp_type: str) -> None:
    """Deletes all opportunities of a specific type for testing purposes only"""

    with instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("DELETE FROM jobs_table WHERE type = %s", (opp_type,))
        connection.commit()


def reset_processed_status(TABLE_NAME: str) -> None:
    """Jobs status will be set to _processed = 0 for testing a debugging purposes"""

    with instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            f"SELECT company, title, location FROM {TABLE_NAME} WHERE processed = 1 LIMIT 5"
        )

        rows = cursor.fetchall()

        for row in rows:
            company, title, location = row[:3]

            cursor.execute(
                f"UPDATE {TABLE_NAME} SET processed = 0 WHERE company = %s AND title = %s AND location = %s",
                (company, title, location),
            )

        connection.commit()
