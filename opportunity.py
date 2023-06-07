from dataclasses import dataclass
from dotenv import load_dotenv
import gpt4free
from gpt4free import Provider
from typing import List, Optional
import os
import ast
from time import sleep
import json
import utility as utils

load_dotenv()

table_name = os.getenv("DB_TABLE")

MAX_RETRY = 15  # Max number of retrys for the gpt_job_analyzer() function


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


def list_opportunities(debug: bool, filtered=False) -> List[Opportunity]:
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


def parse_gpt_values(gpt_response) -> List[bool]:
    """Helper function to parse the gpt response from a str -> List[bool]"""

    return json.loads(gpt_response)


def filter_out_opportunities(list_of_opps, gpt_response) -> List[Opportunity]:
    """Helper function for gpt_job_analyzer() to filter the data"""
    structured_opps = [
        opp for opp, response in zip(list_of_opps, gpt_response) if response
    ]

    print(f"Length after GPT analyzed the jobs: {len(structured_opps)}")
    return structured_opps


def get_parsed_values(prompt) -> List[bool]:
    """Helper function which returns the parsed values response from GPT"""
    response = gpt4free.Completion.create(
        Provider.You,
        prompt=prompt,
    )

    parsed_values = parse_gpt_values(response)

    return parsed_values


def gpt_job_analyzer(list_of_opps) -> List[Opportunity]:
    """Analyzes each job opportunity before being inserted into the DB"""

    print(f"The jobs original length before filtering: {len(list_of_opps)}")

    prompt = "Your role is to assess job opportunities for college students in the tech industry, particularly those pursuing Computer Science majors and seeking entry-level positions. To aid in this decision-making process, please provide a list of booleans (True/False) for each job that aligns with our goal of offering entry-level tech-related positions to college students. Please state the list of booleans directly as minified JSON array of boolean values, without any additional text or comments."

    for opp in list_of_opps:
        prompt += f"\nCompany: {opp._company}"
        prompt += f"\nTitle: {opp._title}"
        prompt += f"\nLocation: {opp._location}"
        prompt += "\n"

    parsed_values = []
    for _ in range(MAX_RETRY):  # Keep looping until a valid prompt is recieved
        try:
            parsed_values = get_parsed_values(prompt)
            break
        except (
            json.decoder.JSONDecodeError
        ):  # The type of error that would be recieved is type JSON
            sleep(0.5)

    if (
        len(parsed_values) == 0
    ):  # If the parsed values ends up being 0 then exit() the entire function
        print("Filtered jobs from GPT are 0. Exiting...")
        exit()

    return filter_out_opportunities(
        list_of_opps, parsed_values
    )  # Returns filtered out opportunities if len(parsed_values) > 0
