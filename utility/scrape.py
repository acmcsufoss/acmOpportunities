from utility.opportunity import Opportunity, OpportunityType
from typing import List
import utility.utils as utils
import os
from dotenv import load_dotenv
import re
import requests

load_dotenv()
utils.verify_set_env_variables()

MAX_OPPORTUNITY_LIST_LENGTH = 15

# ----------------- INTERNSHIP DATA -----------------


def request_github_internship24_data() -> List[Opportunity]:
    """Scrapes Internship Data '24 from Github Repo"""

    github_list = []

    url = os.getenv("GH_INTERN24_URL")
    parse_content = utils.content_parser(url)
    td_elems = parse_content.find_all("tr")

    for cell in td_elems[1:]:
        if len(github_list) <= MAX_OPPORTUNITY_LIST_LENGTH:
            elements = cell.find_all("td")

            company = elements[0].text
            title = elements[1].text
            location = elements[2].text
            link = elements[3]
            if "🔒" not in link.text:
                opportunity = Opportunity(
                    company,
                    title,
                    location,
                    link.find("a")["href"],
                    0,
                    OpportunityType.INTERNSHIP.value,
                )
                github_list.append(opportunity)

    return github_list


def request_linkedin_internship24_data() -> List[Opportunity]:
    """Web scrapes Summer '24 Internship Opportunities using LinkedIn"""

    url = os.getenv("LINKEDIN_INTERN_URL")
    parse_content = utils.content_parser(url)

    linkedin_internship_opps = utils.blueprint_opportunity_formatter(
        parse_content,
        "base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
        "hidden-nested-link",
        "base-search-card__title",
        "job-search-card__location",
        "base-card__full-link",
        True,
        MAX_OPPORTUNITY_LIST_LENGTH,
        OpportunityType.INTERNSHIP.value,
    )

    return linkedin_internship_opps


# ----------------- JOB DATA -----------------


def request_rapidapi_indeed_data() -> List[Opportunity]:
    """
    This API call retrieves a formatted response object
    and returns a List[Opportunity] as the result
    """

    url = os.getenv("RAPID_API_URL")
    rapid_api_key = os.getenv("RAPID_API_KEY")

    headers = {
        "X-RapidAPI-Key": rapid_api_key,
        "X-RapidAPI-Host": "indeed12.p.rapidapi.com",
    }

    rapid_jobs = []
    response = requests.get(url, headers=headers).json()

    days_needed_command_value = utils.extract_command_value().days_needed[
        0
    ]  # Extracts command-line value

    for elem in response["hits"]:
        time = elem["formatted_relative_time"]

        numeric = re.search(r"\d+", time)
        formatted_time_integer = int(numeric.group()) if numeric else 0

        if (
            len(rapid_jobs) < MAX_OPPORTUNITY_LIST_LENGTH
            and int(days_needed_command_value) >= formatted_time_integer
        ):
            company = elem["company_name"]
            title = elem["title"]
            location = elem["location"]
            link = f'https://www.indeed.com/viewjob?jk={elem["id"]}&locality=us'
            processed = 0

            opportunity = Opportunity(
                company,
                title,
                location,
                link,
                processed,
                OpportunityType.FULL_TIME.value,
            )

            rapid_jobs.append(opportunity)

    return rapid_jobs


def request_linkedin_data() -> List[Opportunity]:
    """Returns a List[Opportunity] which contains web scraped job content"""

    url = os.getenv("LINKEDIN_URL")
    parse_content = utils.content_parser(url)

    linked_in_jobs = utils.blueprint_opportunity_formatter(
        parse_content,
        "base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
        "hidden-nested-link",
        "base-search-card__title",
        "job-search-card__location",
        "base-card__full-link",
        True,
        MAX_OPPORTUNITY_LIST_LENGTH,
        OpportunityType.FULL_TIME.value,
    )

    return linked_in_jobs
