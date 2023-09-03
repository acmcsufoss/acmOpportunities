import requests
import os
import json
import asyncio
from typing import List
import re
from datetime import date
import utility as utils
import db
import opportunity as opps
from opportunity import Opportunity, OpportunityType
from dotenv import load_dotenv

load_dotenv()  # To obtain keys from the .env file


# ----------------- POSTGRES -----------------

TABLE_NAME = os.getenv("DB_TABLE")
MAX_LIST_LENGTH = 13


def create():
    """Creates the DB. Only needs to be called once."""

    with db.instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME}(company TEXT, title TEXT, location TEXT, link TEXT, processed INTEGER DEFAULT 0)"""
        )

        connection.commit()


# ----------------- INTERNSHIP DATA -----------------


def request_github_internship24_data() -> List[Opportunity]:
    """Scrapes Internship Data '24 from Github Repo"""

    url = os.getenv("GH_INTERN24_URL")
    parse_content = utils.content_parser(url)
    github_list = []
    td_elems = parse_content.find_all("tr")

    for cell in td_elems[1:]:
        if len(github_list) <= MAX_LIST_LENGTH:
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
        MAX_LIST_LENGTH,
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
            len(rapid_jobs) < MAX_LIST_LENGTH
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
        MAX_LIST_LENGTH,
        OpportunityType.FULL_TIME.value,
    )

    return linked_in_jobs


# ----------------- RESET FUNCTION (DEBUGGING PURPOSES) -----------------


def reset_processed_status(TABLE_NAME):
    """Jobs status will be set to _processed = 0 for testing a debugging purposes"""

    with db.instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            f"SELECT company, title, location FROM {TABLE_NAME} WHERE processed = 1 LIMIT 5"
        )

        rows = cursor.fetchall()

        for row in rows:
            company, title, location = row[:3]

            cursor.execute(
                f"UPDATE {TABLE_NAME} SET processed = 0 WHERE company = %s AND title = %s AND location = %s",
                (company, title, location),
            )

        connection.commit()


# ----------------- DISCORD BOT -----------------


async def execute_opportunities_webhook(webhook_url, job_message, internship_message):
    """
    Executes the message which receives the formatted message
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
    # Creates table in database
    with_create_table_command = utils.extract_command_value().create
    if with_create_table_command:
        create()
        print(f"Sucessfully created {TABLE_NAME}!")
        exit()  # Exit the main function to avoid calling other functions

    file_paths = [os.getenv("MESSAGE_PATH"), os.getenv("PROMPTS_PATH")]
    customized_object = utils.user_customization(file_paths)

    # Determines the customized prompts for PaLM
    prompt_object = utils.determine_prompts(customized_object["customized_prompts"])

    # Determines the customized message for the webhook
    finalized_message = utils.determine_customized_message(
        customized_object["customized_message"]
    )

    # Consolidates all job-related opportunities into a comprehensive List[Opportunity], eliminating repetitive calls to the LLM SERVER.
    job_opps = utils.merge_all_opportunity_data(request_linkedin_data())

    filtered_job_opps = utils.gpt_job_analyze(
        job_opps,
        prompt_object["full_time"],
    )
    opps.ingest_opportunities(filtered_job_opps)

    # Consolidates all job-related opportunities into a comprehensive List[Opportunity], eliminating repetitive calls to the LLM SERVER.
    internship_opps = utils.merge_all_opportunity_data(
        request_linkedin_internship24_data(),
        request_github_internship24_data(),
    )

    filtered_internship_opps = utils.gpt_job_analyze(
        internship_opps,
        prompt_object["internship"],
    )
    opps.ingest_opportunities(filtered_internship_opps)

    # To test the code without consuming API requests, call reset_processed_status().
    # This function efficiently resets the processed status of 5 job postings by setting them to _processed = 0.
    # By doing so, developers can run tests without wasting valuable API resources.
    # To do so, please comment the function calls above this comment.
    # After, please uncomment the following line of code:

    # reset_processed_status()

    internship_data_results = opps.list_opportunities(True, "internship", filtered=True)
    job_data_results = opps.list_opportunities(True, "full_time", filtered=True)

    internship_formatted_message = opps.format_opportunities(
        internship_data_results, finalized_message
    )
    job_formatted_message = opps.format_opportunities(
        job_data_results, finalized_message
    )

    discord_webhook = os.getenv("DISCORD_WEBHOOK")

    await execute_opportunities_webhook(
        discord_webhook, job_formatted_message, internship_formatted_message
    )

    opps.update_opportunities_status(job_data_results)
    opps.update_opportunities_status(internship_data_results)


if __name__ == "__main__":
    asyncio.run(main())
