from dataclasses import dataclass
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()

db_uri = os.getenv("DB_URI")
table_name = os.getenv("DB_TABLE")


def instantiates_db_connection():
    """Returns the connection from the DB"""

    return psycopg2.connect(db_uri)


@dataclass
class Opportunity:
    """Class for ..."""

    list_of_objects = [] # A list of objects holding all jobs (processed and not processed)
    job_objects = {}  # A object populated with a job

    def list_all_opportunities(self) -> "Opportunity":  # Return type of opportunity
        """Lists all oppportunities in DB as well as returns them"""

        with instantiates_db_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(f"SELECT * FROM {table_name}")

            rows = cursor.fetchall()

            for row in rows:
                self.job_objects = {}

                self.job_objects["_company"] = row[0]
                self.job_objects["_title"] = row[1]
                self.job_objects["_location"] = row[2]
                self.job_objects["_link"] = row[3]
                self.job_objects["_processed"] = row[4]

                self.list_of_objects.append(self.job_objects)

                # Uncomment to view all jobs

                # _company, _title, _location, _link, _processed = row

                # print("Company:", _company)
                # print("Title:", _title)
                # print("Location:", _location)
                # print("Link:", _link)
                # print("Processed:", _processed)
                # print(" ")

        return self


