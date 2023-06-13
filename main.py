import psycopg2
import requests
import os
import json
import asyncio
from typing import List
import re
from datetime import date
import utility as utils
import opportunity as opps
from opportunity import Opportunity
from dotenv import load_dotenv

load_dotenv()  # To obtain keys from the .env file


# ----------------- POSTGRES -----------------


def create(table_name):
    """Creates the DB. Only needs to be called once."""

    with utils.instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS {table_name}(_company TEXT, _title TEXT, _location TEXT, _link TEXT, _processed INTEGER DEFAULT 0)"""
        )

        connection.commit()


# ----------------- INTERNSHIP DATA -----------------


def request_github_internship24_data() -> List[Opportunity]:
    """Scrapes Internship Data '24 from Github Repo"""

    url = os.getenv("GITHUB_INTERN24_URL")

    parse_content = utils.content_parser(url)

    table_div = parse_content.find_all("tr")
    github_list = []
    for table in table_div:
        cell = table.find_all("td")
        if len(cell) == 3:
            _company = cell[0].find("a")
            _titles = cell[2].find_all(
                "a"
            )  # Create a List[str] which contain all the titles
            _location = cell[1].text

            if (
                (_company and "href" in _company.attrs)
                or any(title and "href" in title.attrs for title in _titles)
                # If the current row has any job titles that contain a link attribute
                and "Closed" not in _titles
            ):
                _company_link = (
                    _company["href"] if _company and len(_titles) == 1 else ""
                )  # If the length of the current title(s) is 1 then we grab the company link immediately
                _company_name = (
                    _company.text.strip() if _company else cell[0].text.strip()
                )

                # Loop through each given title where there could be a possible link to the job
                for title in _titles:
                    _title_text = title.text.strip()
                    _title_link = (
                        title["href"] if "href" in title.attrs else _company_link
                    )  # If there exists a link in the title job section then we just add that as the link, else we add the company link from earlier
                    opportunity = Opportunity(
                        _company_name, _title_text, _location.strip(), _title_link, 0
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
        5,
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

    command_line_value = utils.extract_command_value()  # Extracts command-line value

    for elem in response["hits"]:
        time = elem["formatted_relative_time"]

        numeric = re.search(r"\d+", time)
        formatted_time_integer = int(numeric.group()) if numeric else 0

        if len(rapid_jobs) < 10 and int(command_line_value) >= formatted_time_integer:
            _company = elem["company_name"]
            _title = elem["title"]
            _location = elem["location"]
            _link = f'https://www.indeed.com/viewjob?jk={elem["id"]}&locality=us'
            _processed = 0

            opportunity = Opportunity(_company, _title, _location, _link, _processed)

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
        10,
    )

    return linked_in_jobs


# ----------------- RESET FUNCTION (DEBUGGING PURPOSES) -----------------


def reset_processed_status(table_name):
    """Jobs status will be set to _processed = 0 for testing a debugging purposes"""

    with utils.instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            f"SELECT _company, _title, _location FROM {table_name} WHERE _processed = 1 LIMIT 5"
        )

        rows = cursor.fetchall()

        for row in rows:
            _company, _title, _location = row[:3]

            cursor.execute(
                f"UPDATE {table_name} SET _processed = 0 WHERE _company = %s AND _title = %s AND _location = %s",
                (_company, _title, _location),
            )

        connection.commit()


# ----------------- DISCORD BOT -----------------


async def execute_opportunities_webhook(webhook_url, job_message, internship_message):
    """
    Executes the message which recieves the formatted message
    from the format_opportunities() function as well as the webhook
    url for the respected discord channel
    """

    # Create a dictionary payload for the message content
    payload = {
        "content": "# ✨ NEW OPPORTUNITY POSTINGS BELOW! ✨",
        "tts": False,
        "embeds": [
            {
                "title": f"✧･ﾟ: *✧･ﾟ:* 🎀 {date.today()} 🎀 ✧･ﾟ: *✧･ﾟ:*｡",
                "color": 0xFFFFFF,
            },
        ],
    }

    if job_message:
        payload["embeds"].append(
            {
                "title": "¸„.-•~¹°”ˆ˜¨ JOB OPPORTUNITIES ¨˜ˆ”°¹~•-.„¸",
                "description": job_message,
                "color": 0x05A3FF,
            },
        )

    if internship_message:
        payload["embeds"].append(
            {
                "title": " ¸„.-•~¹°”ˆ˜¨ INTERNSHIP OPPORTUNITIES ¨˜ˆ”°¹~•-.„¸",
                "description": internship_message,
                "color": 0x05A3FF,
            },
        )

    # Convert the payload to JSON format
    json_payload = json.dumps(payload)

    # This will send a POST request to the webhook_url!
    response = requests.post(
        webhook_url, data=json_payload, headers={"Content-Type": "application/json"}
    )

    if response.status_code == 204:
        print("Webhook message was sent sucessfully!")
    else:
        print(f"Failed to send webhook message. Status Code: {response.status_code}")


async def main():
    # Merges all job related opportunities to one large List[Opportunity]
    # job_opps = utils.merge_all_opportunity_data(
    #     request_rapidapi_indeed_data(), request_linkedin_data()
    # )
    # filtered_job_opps = utils.gpt_job_analyze(
    #     job_opps
    # )
    # opps.ingest_opportunities(filtered_job_opps, "jobs_table")

    # Merges all internship related opportunities to one large List[Opportunity]
    # internship_opps = utils.merge_all_opportunity_data(
    #     request_github_internship24_data(),
    #     request_linkedin_internship24_data(),
    # )
    # filtered_internship_opps = utils.gpt_job_analyze(
    #     internship_opps
    # )
    # opps.ingest_opportunities(filtered_internship_opps, "internship_table")

    """
    To test the code without consuming API requests, call reset_processed_status().
    This function efficiently resets the processed status of 5 job postings by setting them to _processed = 0.
    By doing so, developers can run tests without wasting valuable API resources.
    To do so, please comment the function calls above this comment.
    After, please uncomment the following line of code:
    """
    # reset_processed_status()

    # utils.gpt_job_analyzer(request_linkedin_data())
    # internship_data_results = opps.list_opportunities(
    #     True, "internship_table", filtered=True
    # )
    # job_data_results = opps.list_opportunities(True, "jobs_table", filtered=True)

    # if (
    #     len(job_data_results) == 0 or len(internship_data_results) == 0
    # ):
    #     print("There are no job opportunities today.")
    #     exit()

    # internship_formatted_message = opps.format_opportunities(internship_data_results)
    # job_formatted_message = opps.format_opportunities(job_data_results)

    # discord_webhook = os.getenv("DISCORD_WEBHOOK")

    # await execute_opportunities_webhook(
    #     discord_webhook, job_formatted_message, internship_formatted_message
    # )

    # opps.update_opportunities_status(job_data_results, "jobs_table")
    # opps.update_opportunities_status(internship_data_results, "internship_table")


# if __name__ == "__main__":
#     asyncio.run(main())
