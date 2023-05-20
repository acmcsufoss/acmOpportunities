import requests
import os
import json
import asyncio
import discord
import re
from discord import Webhook
from typing import List
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import sqlite3

# For using my .ENV files
load_dotenv()
job_db = os.getenv("JOB_DB")


# -------------------FOR SQLITE----------------------------

# https://docs.python.org/3/library/sqlite3.html
# https://www.blog.pythonlibrary.org/2021/09/30/sqlite/#:~:text=Here%20is%20how%20you%20would%20create%20a%20SQLite,the%20sqlite3%20module%20will%20create%20an%20empty%20database.


def create():
    # Creates the DB. Only needs to be called once.

    connection = sqlite3.connect(job_db)
    cursor = connection.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS jobs(_company TEXT, _title TEXT, _location TEXT, _link TEXT, _processed BOOLEAN DEFAULT 0)"""
    )

    connection.commit()
    connection.close()


def ingest_opportunities(job_data):
    # Inserts opportunities if and only if they do not already exist

    connection = sqlite3.connect(job_db)
    cursor = connection.cursor()

    for job in job_data:
        cursor.execute(
            "SELECT COUNT(*) FROM jobs WHERE _company = ? AND _title = ? AND _location = ?",
            (job["_company"], job["_title"], job["_location"]),
        )
        counter = cursor.fetchone()[0]

        # https://pynative.com/python-cursor-fetchall-fetchmany-fetchone-to-read-rows-from-table/

        # The job does not exist if the counter is 0, insert a new job

        if counter == 0:
            cursor.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?)",
                (job["_company"], job["_title"], job["_location"], job["_link"], 0),
            )

    connection.commit()
    connection.close()


# -------------------FOR RAPIDAPI----------------------------


def rapid_response() -> List[object]:
    url = os.getenv("RAPID_API_URL")

    rapid_api_key = os.getenv("RAPID_API_KEY")
    rapid_api_host = os.getenv("RAPID_API_HOST")

    headers = {
        "X-RapidAPI-Key": rapid_api_key,
        "X-RapidAPI-Host": rapid_api_host,
    }

    rapid_jobs = []
    response = requests.get(url, headers=headers).json()

    # re import info - https://www.geeksforgeeks.org/find-all-the-numbers-in-a-string-using-regular-expression-in-python/

    for elem in response["hits"]:
        time = elem["formatted_relative_time"]
        time_in_lowercase = (
            time.lower()
        )  # Checking for "Today" or "Yesterday" in the relative timestamp
        numeric = re.search(r"\d+", time)
        formatted_time_integer = int(numeric.group()) if numeric else 0

        if (
            formatted_time_integer >= 0
            and formatted_time_integer <= 3
            or "today" in time_in_lowercase
            or "yesterday" in time_in_lowercase
        ):
            if len(rapid_jobs) <= 3:
                job = {}
                job["_company"] = elem["company_name"]
                job["_title"] = elem["title"]
                job["_location"] = elem["location"]
                job[
                    "_link"
                ] = f'https://www.indeed.com/viewjob?jk={elem["id"]}&locality=us'

            print(elem)

            rapid_jobs.append(job)

    return rapid_jobs


# -------------------FOR LINKEDIN----------------------------


def linkedin_response() -> List[object]:
    url = os.getenv("LINKEDIN_URL")

    response = requests.get(url)

    content = response.text

    parse_content = BeautifulSoup(content, "html.parser")

    div_post = parse_content.find_all(
        "div",
        class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
    )

    linked_in_jobs = []

    for elem in div_post:
        if len(linked_in_jobs) <= 2:
            job = {}
            job["_company"] = elem.find(
                "h4", class_="base-search-card__subtitle"
            ).text.strip()
            job["_title"] = elem.find(
                "h3", class_="base-search-card__title"
            ).text.strip()
            job["_location"] = elem.find(
                "span", class_="job-search-card__location"
            ).text.strip()
            job["_link"] = elem.find("a", class_="base-card__full-link")["href"].split(
                "?"
            )[0]

            linked_in_jobs.append(job)

    return linked_in_jobs


# -------------------FOR HELPER FUNCTIONS ----------------------------


def shorten_linkedin_list():
    connection = sqlite3.connect(job_db)
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM jobs WHERE _link LIKE '%linkedin%'")
    rows = cursor.fetchall()

    for row in rows:
        _company = row[0]
        _title = row[1]
        _location = row[2]
        _link = row[3].split("?")[0]
        _processed = row[4]

        cursor.execute(
            "UPDATE jobs SET _link = ? WHERE _company = ? AND _title = ? AND _location = ? ",
            (_link, _company, _title, _location),
        )

    connection.commit()
    connection.close()


# Lists all oppportunities in DB


def list_all_opportunities() -> List[object]:
    connection = sqlite3.connect(job_db)
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM jobs")
    rows = cursor.fetchall()

    for row in rows:
        _company = row[0]
        _title = row[1]
        _location = row[2]
        _link = row[3]
        _processed = row[4]

        print("Company:", _company)
        print("Title:", _title)
        print("Location:", _location)
        print("Link:", _link)
        print("Processed:", _processed)
        print(" ")

    connection.close()


# List opportunities shows all the opportunities that have NOT been posted yet


def list_filtered_opportunities() -> List[object]:
    connection = sqlite3.connect(job_db)
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM jobs WHERE _processed = 0 LIMIT 5")
    rows = cursor.fetchall()

    not_processed_rows = []

    for row in rows:
        job = {}

        job["_company"] = row[0]
        job["_title"] = row[1]
        job["_location"] = row[2]
        job["_link"] = row[3]
        job["_processed"] = row[4]

        # Uncomment to view jobs up to 5 that have not been posted

        # print("Company:", row[0])
        # print("Title:", row[1])
        # print("Location:", row[2])
        # print("Link:", row[3])
        # print("Processed:", row[4])
        # print(" ")

        not_processed_rows.append(job)

    connection.close()
    return not_processed_rows


# Recieves data from list_filtered_opporunities() and formats them into a single string


def format_opportunities(data_results) -> str:
    formatted_string = ""

    for data_block in data_results:
        _company = data_block["_company"]
        _title = data_block["_title"]
        _location = data_block["_location"]
        _link = data_block["_link"]

        formatted_string += f"✨✨ NEW OPPORTUNITY!!! ✨✨ {_company} is NOW hiring for {_title} @{_location}! {_link}\n\n"

    print(formatted_string)
    return formatted_string


# Updates the status of the jobs after it's been sent by the Discord Bot


def update_opportunities_status(data_results):
    connection = sqlite3.connect(job_db)
    cursor = connection.cursor()

    for data_block in data_results:
        cursor.execute(
            "UPDATE jobs SET _processed = ? WHERE _company = ? AND _title = ? AND _location = ? ",
            (1, data_block["_company"], data_block["_title"], data_block["_location"]),
        )

    connection.commit()
    connection.close()


# -------- RESET FUNCTION FOR TESTING PURPOSES -------

# Jobs will be set to not processed (or 0) for testing a debugging purposes


def reset_processed_status():
    connection = sqlite3.connect(job_db)
    cursor = connection.cursor()

    cursor.execute("SELECT _company, _title, _location FROM jobs WHERE _processed = 1")
    rows = cursor.fetchall()

    for row in rows:
        _company = row[0]
        _title = row[1]
        _location = row[2]

        cursor.execute(
            "UPDATE jobs SET _processed = 0 WHERE _company = ? AND _title = ? AND _location = ?",
            (_company, _title, _location),
        )

    connection.commit()
    connection.close()


# -------------------FOR DISCORD BOT----------------------------


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def execute_opportunities_webhook(webhook_url, message):
    # Create a dictionary payload for the message content
    payload = {"content": message}

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


# -----------------EXECUTE FUNCTIONS-----------------


rapid_data = rapid_response()
linkedin_data = linkedin_response()

ingest_opportunities(rapid_data)
ingest_opportunities(linkedin_data)


data_results = list_filtered_opportunities()
formatted_message = format_opportunities(data_results)


async def main():
    discord_webhook = os.getenv("DISCORD_WEBHOOK")

    await execute_opportunities_webhook(discord_webhook, formatted_message)

    update_opportunities_status(data_results)


if __name__ == "__main__":
    asyncio.run(main())

# Please note all jobs right now have been set to _processed = 0 for testing purposes.
# Will delete everything from the DB due to inconsistencies, and will continue with the final product from here on.
list_all_opportunities()
