from datetime import date, datetime
import psycopg2
import os

def instantiates_db_connection():
    """Returns the connection from the DB"""
    
    db_uri = os.getenv("DB_URI")
    return psycopg2.connect(db_uri)


def calculate_day_difference(job_post_date: datetime) -> int:
    today_date_str = date.today().strftime("%Y-%m-%d") # https://www.geeksforgeeks.org/python-strftime-function/
    our_date_object = datetime.strptime(today_date_str, "%Y-%m-%d") # https://www.geeksforgeeks.org/python-datetime-strptime-function/

    return our_date_object.day - job_post_date.day

