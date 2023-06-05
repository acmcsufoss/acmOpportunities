from datetime import date, datetime
import psycopg2
import os


def instantiate_db_connection():
    """Returns the connection from the DB"""

    db_uri = os.getenv("DB_URI")
    return psycopg2.connect(db_uri)


def calculate_day_difference(job_post_date: datetime) -> int:
    """Calculates day difference for job posting times to the relevant day today"""

    today_date = date.today()
    job_date = job_post_date.date()

    # https://www.geeksforgeeks.org/python-datetime-toordinal-method-with-example/
    today_ordinal = today_date.toordinal()
    job_ordinal = job_date.toordinal()

    day_difference = today_ordinal - job_ordinal

    return day_difference
