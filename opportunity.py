from dataclasses import dataclass
from dotenv import load_dotenv
import psycopg2
from typing import List
import os
import utility as utils 

load_dotenv()

table_name = os.getenv("DB_TABLE")

@dataclass
class Opportunity:
    """Class for ..."""
    # TODO


def list_all_opportunities() -> List[object]:  # Return type of opportunity
    """Lists all oppportunities in DB as well as returns them"""

    with utils.instantiates_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(f"SELECT * FROM {table_name}")

        rows = cursor.fetchall()

        list_of_objects = []

        for row in rows:
            job_objects = {}

            job_objects["_company"] = row[0]
            job_objects["_title"] = row[1]
            job_objects["_location"] = row[2]
            job_objects["_link"] = row[3]
            job_objects["_processed"] = row[4]

            list_of_objects.append(job_objects)

            # Uncomment to view all jobs

            # _company, _title, _location, _link, _processed = row

            # print("Company:", _company)
            # print("Title:", _title)
            # print("Location:", _location)
            # print("Link:", _link)
            # print("Processed:", _processed)
            # print(" ")

    return list_of_objects



        
def list_filtered_opportunities() -> List[object]:
    """Returns a List[object] of job data that have a status of _processed = 0"""

    with utils.instantiates_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(f"SELECT * FROM {table_name} WHERE _processed = 0 LIMIT 20")
        rows = cursor.fetchall()

        list_of_objects = []

        for row in rows:
            job_objects = {}

            job_objects["_company"] = row[0]
            job_objects["_title"] = row[1]
            job_objects["_location"] = row[2]
            job_objects["_link"] = row[3]
            job_objects["_processed"] = row[4]

                # Uncomment to view up to 10 jobs that have not been posted

                # _company, _title, _location, _link, _processed = row

                # print("Company:", _company)
                # print("Title:", _title)
                # print("Location:", _location)
                # print("Link:", _link)
                # print("Processed:", _processed)
                # print(" ")

            list_of_objects.append(job_objects)

    return list_of_objects


