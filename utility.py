from datetime import date, datetime
import psycopg2
import requests
from typing import List
import os
import argparse
from bs4 import BeautifulSoup
from opportunity import Opportunity


# ----------------- FOR CLI LIBRARY COMMAND -----------------


def extract_command_value() -> str:
    """Returns the value of type str prompted in the command line following --days-needed"""

    parser = argparse.ArgumentParser(
        description="Custom command for specifying days for fetching jobs."
    )

    # Add an argument (the custom command) along with the help functionality to see what the command does
    parser.add_argument(
        "--days-needed", type=str, help="The number of days needed to fetch jobs."
    )

    # Parse the argument and insert into a variable
    arguments = parser.parse_args()

    # Create a new variable to access the --days-needed command
    days_needed_variable = arguments.days_needed

    # Return the value from the --days-needed custom command
    return days_needed_variable


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
    company_elem,  # Class to recieve the company text
    title_elem,  # Class to recieve the title text
    location_elem,  # Class to recieve the location text
    link_elem,  # Class to recieve the link
    date_limit: bool,  # If true will compare the command line value to date difference, else will not be accounted for in the final list
    len_of_jobs: int,  # Determines how many jobs will be stored in the final List[Opportunity]
) -> List[Opportunity]:
    """Helper function which serves as a data extraction blueprint for specific formatting"""

    div = content.find_all("div", class_=div_elem)
    command_line_value = extract_command_value()
    internship_list = []
    for elem in div:
        _company = elem.find(class_=company_elem).text.strip()
        _title = elem.find(class_=title_elem).text.strip()
        _location = elem.find(class_=location_elem).text.strip()
        _link = elem.find(class_=link_elem)["href"].split("?")[0]
        _processed = 0

        date_difference = calculate_day_difference(elem)
        if len(internship_list) < len_of_jobs:
            if date_limit and int(command_line_value) >= date_difference:
                opportunity = Opportunity(
                    _company, _title, _location, _link, _processed
                )
            else:
                opportunity = Opportunity(
                    _company, _title, _location, _link, _processed
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

    print(merged_opp_list)
    return merged_opp_list
