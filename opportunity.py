from dataclasses import dataclass
from dotenv import load_dotenv
from typing import List, Optional
import utility as utils


load_dotenv()


@dataclass
class Opportunity:
    """Struct to hold data for an opportunity"""

    _company: str
    _title: str
    _location: str
    _link: str
    _processed: bool


def ingest_opportunities(job_data, table_name):
    """Inserts opportunities if and only if they do not already exist"""
    with utils.instantiate_db_connection() as connection:
        cursor = connection.cursor()

        for job in job_data:
            cursor.execute(
                f"SELECT * FROM {table_name} WHERE _company = %(_company)s AND _title = %(_title)s AND _location = %(_location)s",
                {
                    "_company": job._company,
                    "_title": job._title,
                    "_location": job._location,
                },
            )
            row = cursor.fetchone()

            if row is None:
                cursor.execute(
                    f"INSERT INTO {table_name} (_company, _title, _location, _link, _processed) VALUES (%s, %s, %s, %s, %s)",
                    (
                        job._company,
                        job._title,
                        job._location,
                        job._link,
                        job._processed,
                    ),
                )
        connection.commit()


def list_opportunities(
    debug: bool,
    table_name,
    filtered=False,
) -> List[Opportunity]:
    """Lists all oppportunities in DB as well as returns them"""

    with utils.instantiate_db_connection() as connection:
        cursor = connection.cursor()

        if filtered:
            cursor.execute(f"SELECT * FROM {table_name} WHERE _processed = 0 LIMIT 15")
        else:
            cursor.execute(f"SELECT * FROM {table_name}")

        rows = cursor.fetchall()

        return read_all_opportunities(rows, debug)


def read_all_opportunities(rows, debug_tool) -> List[Opportunity]:
    """Helper function designed to return filtered or unfiltered opportunities"""
    opportunities = []

    for row in rows:
        _company, _title, _location, _link, _processed = row

        if debug_tool:
            print("Company:", _company)
            print("Title:", _title)
            print("Location:", _location)
            print("Link:", _link)
            print("Processed:", _processed)
            print(" ")

        opportunity = Opportunity(_company, _title, _location, _link, _processed)

        opportunities.append(opportunity)

    return opportunities


def update_opportunities_status(data_results, table_name):
    """Updates the status of the jobs to _processed = 1 after it's been sent by the discord bot"""

    with utils.instantiate_db_connection() as connection:
        cursor = connection.cursor()

        for data_block in data_results:
            cursor.execute(
                f"UPDATE {table_name} SET _processed = %s WHERE _company = %s  AND _title = %s  AND _location = %s",
                (
                    1,
                    data_block._company,
                    data_block._title,
                    data_block._location,
                ),
            )

        connection.commit()


def format_opportunities(data_results) -> str:
    """Recieves data from list_filtered_opporunities() and returns a single string message"""

    formatted_string = ""

    for data_block in data_results:
        _company = data_block._company
        _title = data_block._title
        _location = data_block._location
        _link = data_block._link

        formatted_string += f"[**{_company}**]({_link}): {_title} `@{_location}`!\n"

    return formatted_string
