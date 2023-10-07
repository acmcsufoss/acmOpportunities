from datetime import date, datetime
import requests
from typing import List
import os
import argparse
import json
from bs4 import BeautifulSoup
from utility.opportunity import Opportunity
from utility.blocklist import BlockList

# ----------------- FOR CLI LIBRARY COMMAND -----------------


def extract_command_value():
    """Returns the value of type str prompted in the command line following --days-needed"""

    parser = argparse.ArgumentParser(
        description="Custom command for specifying days for fetching jobs."
    )

    # Add an argument (the custom command) along with the help functionality to see what the command does
    parser.add_argument(
        "--days-needed",
        type=str,
        nargs=1,
        help="The amount of days to extract jobs.",
    )

    parser.add_argument(
        "--create", action="store_true", help="Creates the table in your database."
    )

    # Parse the argument and insert into a variable
    arguments = parser.parse_args()

    return arguments


def verify_set_env_variables() -> any:
    """Determines if the env variables are all set properly"""

    env_variables = [
        "LINKEDIN_URL",
        "DISCORD_WEBHOOK",
        "DB_URI",
        "DB_TABLE",
        "PALM_API_KEY",
        "GH_INTERN24_URL",
        "LINKEDIN_INTERN_URL",
        "PROMPTS_PATH",
        "MESSAGE_PATH",
    ]

    # Checks to see if the env variables in env_variables
    # all exist in the current variables
    if not set(os.environ).issuperset(env_variables):
        raise EnvironmentError("One or more env variables are not set.")


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
    days_needed_command_value = extract_command_value().days_needed[0]
    internship_list = []
    for elem in div:
        company = elem.find(class_=company_elem).text.strip()
        if not BlockList().is_blacklisted_company(company):
            title = elem.find(class_=title_elem).text.strip()
            location = elem.find(class_=location_elem).text.strip()
            link = elem.find(class_=link_elem)["href"].split("?")[0]
            processed = 0

            date_difference = calculate_day_difference(elem)

            if len(internship_list) < len_of_jobs:
                if date_limit and int(days_needed_command_value) >= date_difference:
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


def user_customization(file_paths: List[str]) -> dict:
    """Returns users customization for both message and prompt"""

    data = []

    for file_path in file_paths:
        try:
            with open(file_path, "r") as file:
                text = file.read()
                data.append(text)
        except OSError:
            print(f"Unable to open/read file path: '{file_path}'")

    return {"customized_message": data[0], "customized_prompts": data[1]}


def determine_prompts(customized_prompts: dict) -> object:
    """Determines the final PaLM prompt"""

    final_prompt_object = {}
    prompts = json.loads(customized_prompts)[0]

    final_prompt_object["full_time"] = prompts["OpportunityType.FULL_TIME"]
    final_prompt_object["internship"] = prompts["OpportunityType.INTERNSHIP"]

    return final_prompt_object


def determine_customized_message(message: dict) -> str:
    """Determines the customized text for the webhook"""
    default = "[**{company}**]({link}): {title} `@{location}`!"

    file_message = json.loads(message)[0]

    return file_message["Message"] if file_message["Message"] else default
