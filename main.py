import psycopg2
import requests
import os
import json
import asyncio
import argparse
from typing import List
from bs4 import BeautifulSoup
import re
from datetime import date, datetime
import utility as utils
import opportunity as opps
from dotenv import load_dotenv

load_dotenv()  # To obtain keys from the .env file


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


# ----------------- FOR POSTGRES -----------------
table_name = os.getenv("DB_TABLE")


def create():
    """Creates the DB. Only needs to be called once."""

    with utils.instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS {table_name}(_company TEXT, _title TEXT, _location TEXT, _link TEXT, _processed INTEGER DEFAULT 0)"""
        )

        connection.commit()


def ingest_opportunities(job_data):
    """Inserts opportunities if and only if they do not already exist"""

    with utils.instantiate_db_connection() as connection:
        cursor = connection.cursor()

        for job in job_data:
            cursor.execute(
                f"SELECT * FROM {table_name} WHERE _company = %(_company)s AND _title = %(_title)s AND _location = %(_location)s",
                {
                    "_company": job["_company"],
                    "_title": job["_title"],
                    "_location": job["_location"],
                },
            )
            row = cursor.fetchone()

            if row is None:
                cursor.execute(
                    f"INSERT INTO {table_name} (_company, _title, _location, _link, _processed) VALUES (%s, %s, %s, %s, %s)",
                    (job["_company"], job["_title"], job["_location"], job["_link"], 0),
                )
        connection.commit()


# ----------------- JOB DATA -----------------


def request_rapidapi_indeed_data() -> List[object]:
    """
    This API call retrieves a formatted response object
    and returns a List[object] as the result
    """

    url = os.getenv("RAPID_API_URL")
    rapid_api_key = os.getenv("RAPID_API_KEY")

    headers = {
        "X-RapidAPI-Key": rapid_api_key,
        "X-RapidAPI-Host": "indeed12.p.rapidapi.com",
    }

    rapid_jobs = []
    response = requests.get(url, headers=headers).json()

    command_line_value = extract_command_value()  # Extracts command-line value

    for elem in response["hits"]:
        time = elem["formatted_relative_time"]

        numeric = re.search(r"\d+", time)
        formatted_time_integer = int(numeric.group()) if numeric else 0

        if len(rapid_jobs) < 10 and int(command_line_value) > formatted_time_integer:
            job = {}
            job["_company"] = elem["company_name"]
            job["_title"] = elem["title"]
            job["_location"] = elem["location"]
            job["_link"] = f'https://www.indeed.com/viewjob?jk={elem["id"]}&locality=us'

            if (
                "senior" not in job["_title"].lower()
                and "sr" not in job["_title"].lower()
            ):  # Filters out senior positions to ensure entry only level positions
                rapid_jobs.append(job)

    return rapid_jobs


def request_linkedin_data() -> List[object]:
    """Returns a List[object] which contains web scraped job content"""

    url = os.getenv("LINKEDIN_URL")

    response = requests.get(url)

    content = response.text

    parse_content = BeautifulSoup(content, "html.parser")

    div_post = parse_content.find_all(
        "div",
        class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
    )  # TODO Narrow this down where it still recieves the same result

    command_line_value = extract_command_value()  # Extracts command-line value

    linked_in_jobs = []

    for elem in div_post:
        all_dates = elem.find("time")
        datetime_val = all_dates.get("datetime")
        date_object = datetime.strptime(datetime_val, "%Y-%m-%d")

        day_differences = utils.calculate_day_difference(date_object)
        # Calculates date difference from job postings to the relevant day

        if len(linked_in_jobs) < 10 and int(command_line_value) > day_differences:
            job = {}
            job["_company"] = elem.find("a", class_="hidden-nested-link").text.strip()
            job["_title"] = elem.find(
                "h3", class_="base-search-card__title"
            ).text.strip()
            job["_location"] = elem.find(
                "span", class_="job-search-card__location"
            ).text.strip()
            job["_link"] = elem.find("a", class_="base-card__full-link")["href"]

            if (
                "senior" not in job["_title"].lower()
                and "sr" not in job["_title"].lower()
            ):  # Filters out senior positions to ensure entry only level positions
                linked_in_jobs.append(job)
    return linked_in_jobs


# ----------------- HELPER FUNCTIONS -----------------


def format_opportunities(data_results) -> str:
    """Recieves data from list_filtered_opporunities() and returns a single string message"""

    formatted_string = ""

    for data_block in data_results:
        _company = data_block["_company"]
        _title = data_block["_title"]
        _location = data_block["_location"]
        _link = data_block["_link"]

        formatted_string += f"[**{_company}**]({_link}): {_title} `@{_location}`!\n"

    return formatted_string


# ----------------- RESET FUNCTION (DEBUGGING PURPOSES) -----------------


def reset_processed_status():
    """Jobs status will be set to _processed = 0 for testing a debugging purposes"""

    with utils.instantiate_db_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            f"SELECT _company, _title, _location FROM {table_name} WHERE _processed = 1 LIMIT 20"
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


async def execute_opportunities_webhook(webhook_url, message):
    """
    Executes the message which recieves the formatted message
    from the format_opportunities() function as well as the webhook
    url for the respected discord channel
    """

    # Create a dictionary payload for the message content
    payload = {
        "content": "# ✨ NEW JOB POSTINGS BELOW! ✨",
        "tts": False,
        "embeds": [
            {
                "title": f"¸„.-•~¹°”ˆ˜¨   🎀 {date.today()} 🎀   ¨˜ˆ”°¹~•-.„¸",
                "description": message,
                "color": 0x05A3FF,
            }
        ],
    }

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
    # rapid_data = request_rapidapi_indeed_data()
    # linkedin_data = request_linkedin_data()

    # TODO - Call the function opps.gpt_job_analyzer() for both rapid_data and linkedin_data
    # TODO - After calling this function, store in a variable and then call ingest_opportunities() using that variable as an argument
    # Example for testing -> opps.gpt_job_analyzer(request_linkedin_data())

    # ingest_opportunities(rapid_data)
    # ingest_opportunities(linkedin_data)

    """
    To test the code without consuming API requests, call reset_processed_status().
    This function efficiently resets the processed status of all job postings by setting them to _processed = 0.
    By doing so, developers can run tests without wasting valuable API resources.
    To do so, please comment the function calls above this comment.
    After, please uncomment the following line of code:
    """
    # reset_processed_status()

    # data_results = opps.list_filtered_opportunities(True)
    # if len(data_results) == 0:
    #     print("There are no job opportunities today.")
    #     exit()

    # formatted_message = format_opportunities(data_results)

    # discord_webhook = os.getenv("DISCORD_WEBHOOK")

    # await execute_opportunities_webhook(discord_webhook, formatted_message)

    # opps.update_opportunities_status(data_results)


# if __name__ == "__main__":
#     asyncio.run(main())
