from datetime import date, datetime
import psycopg2
import requests
from typing import List
import os
import argparse
from time import sleep
import json
import google.generativeai as palm
from bs4 import BeautifulSoup
from opportunity import Opportunity

# ----------------- FOR CLI LIBRARY COMMAND -----------------


def extract_command_value():
    """Returns the value of type str prompted in the command line following --days-needed"""

    parser = argparse.ArgumentParser(
        description="Custom command for specifying days for fetching jobs."
    )

    # Add an argument (the custom command) along with the help functionality to see what the command does
    parser.add_argument(
        "--days-needed", type=str, help="The number of days needed to fetch jobs."
    )

    parser.add_argument(
        "--create", action="store_true", help="Creates the table in your database."
    )

    # Parse the argument and insert into a variable
    arguments = parser.parse_args()

    # # Create a new variable to access the --days-needed command
    # days_needed_variable = arguments.days_needed

    # create_table = arguments.create

    # # Return the value from the --days-needed custom command
    return arguments


def instantiate_db_connection():
    """Returns the connection from the DB"""

    db_uri = os.getenv("DB_URI")
    return psycopg2.connect(db_uri)


def calculate_day_difference(elem: datetime) -> int:
    """Calculates day difference for job posting times to the relevant day today"""

    all_dates = elem.find("time")
    datetime_val = all_dates.get("datetime")
    date_object = datetime.strptime(datetime_val, "%Y-%m-%d")

    today_date = date.today()
    job_date = date_object.date()

    # https://www.geeksforgeeks.org/python-datetime-toordinal-method-with-example/
    today_ordinal = today_date.toordinal()
    job_ordinal = job_date.toordinal()

    day_difference = today_ordinal - job_ordinal

    return day_difference


def blueprint_opportunity_formatter(
    content,  # Parsed content
    div_elem,  # Class to traverse job elements
    company_elem,  # Class to receive the company text
    title_elem,  # Class to receive the title text
    location_elem,  # Class to receive the location text
    link_elem,  # Class to receive the link
    date_limit: bool,  # If true will compare the command line value to date difference, else will not be accounted for in the final list
    len_of_jobs: int,  # Determines how many jobs will be stored in the final List[Opportunity]
    opp_type: str,
) -> List[Opportunity]:
    """Helper function which serves as a data extraction blueprint for specific formatting"""

    div = content.find_all("div", class_=div_elem)
    command_line_value = extract_command_value().days_needed
    internship_list = []
    for elem in div:
        company = elem.find(class_=company_elem).text.strip()
        title = elem.find(class_=title_elem).text.strip()
        location = elem.find(class_=location_elem).text.strip()
        link = elem.find(class_=link_elem)["href"].split("?")[0]
        processed = 0

        date_difference = calculate_day_difference(elem)
        if len(internship_list) < len_of_jobs:
            if date_limit and int(command_line_value) >= date_difference:
                opportunity = Opportunity(
                    company, title, location, link, processed, opp_type
                )
            else:
                opportunity = Opportunity(
                    company, title, location, link, processed, opp_type
                )

            internship_list.append(opportunity)

    return internship_list


def content_parser(url) -> BeautifulSoup:
    """Helper function to return parsed content"""

    response = requests.get(url)
    content = response.text

    return BeautifulSoup(content, "html.parser")


def merge_all_opportunity_data(*args) -> List[Opportunity]:
    """Merges all the opportunities into one large List[Opportunity]"""
    merged_opp_list = []

    for arg in args:
        merged_opp_list += arg

    return merged_opp_list


def add_column(column_name, default) -> None:
    """Adds a column for adjustment to the table after the table has been created"""
    with instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            f"ALTER TABLE jobs_table ADD COLUMN {column_name} VARCHAR(255) DEFAULT '{default}'"
        )

        connection.commit()


def delete_alL_opportunity_type(opp_type: str) -> None:
    """Deletes all opportunities of a specific type for testing purposes only"""
    with instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("DELETE FROM jobs_table WHERE type = %s", (opp_type,))
        connection.commit()


# ----------------- PALM API -----------------


MAX_RETRY = 5  # Max number of retrys for the gpt_job_analyzer() function
palm.configure(api_key=os.getenv("PALM_API_KEY"))


def current_model_inuse() -> any:
    """Returns the model in use"""

    models = [
        m
        for m in palm.list_models()
        if "generateText" in m.supported_generation_methods
    ]

    model = models[0].name

    return model


def parse_gpt_values(gpt_response) -> List[bool]:
    """Helper function to parse the gpt response from a str -> List[bool]"""
    return json.loads(gpt_response.lower())


def filter_out_opportunities(list_of_opps, gpt_response) -> List[Opportunity]:
    """Helper function for gpt_job_analyzer() to filter the data"""
    structured_opps = [
        opp for opp, response in zip(list_of_opps, gpt_response) if response
    ]

    print(f"Length after GPT analyzed the jobs: {len(structured_opps)}")
    return structured_opps


def get_parsed_values(prompt) -> List[bool]:
    """Function which returns parsed values if the opportunity mathces with the clubs values"""

    defaults = {
        "model": "models/text-bison-001",
        "temperature": 0.0,
        "candidate_count": 1,
        "top_k": 100,
        "top_p": 0.95,
        "max_output_tokens": 3072,
        "stop_sequences": [],
        "safety_settings": [
            {"category": "HARM_CATEGORY_DEROGATORY", "threshold": 3},
            {"category": "HARM_CATEGORY_TOXICITY", "threshold": 3},
            {"category": "HARM_CATEGORY_VIOLENCE", "threshold": 3},
            {"category": "HARM_CATEGORY_SEXUAL", "threshold": 3},
            {"category": "HARM_CATEGORY_MEDICAL", "threshold": 3},
            {"category": "HARM_CATEGORY_DANGEROUS", "threshold": 3},
        ],
    }

    completion = palm.generate_text(**defaults, prompt=prompt)

    parsed_values = parse_gpt_values(completion.result)
    return parsed_values


def gpt_job_analyze(list_of_opps: List[Opportunity], prompt: str) -> List[Opportunity]:
    """Analyzes each job opportunity before being inserted into the DB"""

    print(f"The jobs original length before filtering: {len(list_of_opps)}")

    for opp in list_of_opps:
        prompt += f"\nCompany: {opp.company}"
        prompt += f"\nTitle: {opp.title}"
        prompt += f"\nLocation: {opp.location}"
        prompt += "\n"

    parsed_values = []
    for _ in range(MAX_RETRY):  # Keep looping until a valid prompt is received
        try:
            parsed_values = get_parsed_values(prompt)
            break
        except (
            json.decoder.JSONDecodeError
        ):  # The type of error that would be received is type JSON
            sleep(0.5)

    print(f" Below are the parsed values from GPT\n {parsed_values}")
    print(parsed_values)  # For debugging purposes

    return filter_out_opportunities(
        list_of_opps, parsed_values
    )  # Returns filtered out opportunities
