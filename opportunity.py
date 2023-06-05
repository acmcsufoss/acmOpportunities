from dataclasses import dataclass
from dotenv import load_dotenv
import gpt4free
from gpt4free import Provider
from typing import List, Optional
import os
import ast
import utility as utils

load_dotenv()

table_name = os.getenv("DB_TABLE")


@dataclass
class Opportunity:
    """Struct to hold data for an opportunity"""

    _company: str
    _title: str
    _location: str
    _link: str
    _processed: bool


def ingest_opportunities(job_data):
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


def list_all_opportunities(debug: bool) -> List[Opportunity]:
    """Lists all oppportunities in DB as well as returns them"""

    with utils.instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(f"SELECT * FROM {table_name}")

        rows = cursor.fetchall()

        return read_all_opportunities(rows, debug)


def list_filtered_opportunities(debug: bool) -> List[Opportunity]:
    """Returns a List[object] of job data that have a status of _processed = 0"""

    with utils.instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(f"SELECT * FROM {table_name} WHERE _processed = 0 LIMIT 15")

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


def update_opportunities_status(data_results):
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


def gpt_job_analyzer(list_of_opps) -> List[Opportunity]:
    """Analyzes each job opportunity before being inserted into the DB"""

    print(f"The jobs original length before filtering: {len(list_of_opps)}")

    prompt = "As a member of the Association of Computer Machinery (ACM) club at California State University, Fullerton, your role is to assess job opportunities for college students in the tech industry, particularly those pursuing Computer Science majors and seeking entry-level positions. Your objective is to evaluate each opportunity and decide whether it should be included in our program. To aid in this decision-making process, please provide a True/False as a list of booleans List[bool] (so no quotes) for each job that aligns with our goal of offering entry-level tech-related positions to college students. Please state True/False as a List of booleans List[bool] only one after only, again only since I need to parse this. Do not add any job description or comments, just only say True/False in a proper list as I need to parse this response. \n\n"

    for opp in list_of_opps:
        prompt += "\nCompany: " + opp["_company"]
        prompt += "\nTitle: " + opp["_title"]
        prompt += "\nLocation: " + opp["_location"]
        prompt += "\n"

    response = gpt4free.Completion.create(
        Provider.You,
        prompt=prompt,
    )

    parsed_values = parse_gpt_values(response)

    return determine_job_list(list_of_opps, parsed_values)


def parse_gpt_values(gpt_response) -> List[bool]:
    """Helper function to parse the gpt response from a str -> List[bool]"""
    # https://docs.python.org/3/library/ast.html - Go down to .literal_eval()
    # https://www.geeksforgeeks.org/python-isinstance-method/

    parsed_values = ast.literal_eval(gpt_response)
    bool_list = []
    if isinstance(parsed_values, list):
        bool_list = [bool(value) for value in parsed_values]

    return bool_list


def determine_job_list(list_of_opps, gpt_response) -> List[Opportunity]:
    """Helper function for gpt_job_analyzer() to structure the data in the correct format"""
    structured_opps = []

    for indx, opp in enumerate(list_of_opps):
        if gpt_response[
            indx
        ]:  # If the current response is True (of type bool) create a new Opportunity and append to the list
            opportunity = Opportunity(
                opp["_company"], opp["_title"], opp["_location"], opp["_link"], 0
            )
            structured_opps.append(opportunity)
    print(f"Length after GPT analyzed the jobs: {len(structured_opps)}")
    return structured_opps
