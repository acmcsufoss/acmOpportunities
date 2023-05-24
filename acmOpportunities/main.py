import requests
import os
import json
import asyncio
import discord
import re
import sqlite3
import argparse
from discord import Webhook
from typing import List
from bs4 import BeautifulSoup
from datetime import datetime, date
from dotenv import load_dotenv

# For using my .ENV files
load_dotenv()
job_db = os.getenv("JOB_DB")

# -----------------FOR CLI LIBRARY COMMAND-------------

# ----argparse custom command line thoughts----


# --days-needed-up-to command will be run for jobs that are from the day that it was executed to the amount of days wanted

# For instance, if we wanted all the jobs from today up to 2 days, we can say something like "python main.py --days-needed-up-to 3" (I'll explain why its 3 and NOT 2)

# To go about this, we can create a simple loop through each webscraping/api call (which I already do BUT we will then add a conditional to this loop)

# For web scraping for instance, we can compare the input of our --days-needed-up-to command (3), with the day that it was posted for the linkedin posts

# For the API call, each object has when the job was posted via "formatted_related_time_stamp" in the object.

# We could definitely either create a list or even go the easier route and create a conditional. Look below for what I mean.

# Lets say we have a List[any] called "relative_time_stamps" that contain the relative timestamp of when it was posted

# Lets say the List[any] (relative_time_stamp) contains -> ["Today", "Today", "Yesterday", "2", "2", "3", "5"]

# What we can do is compare the number from the command line (--days-needed-up-to) to this list

# So "3" != "Today" so we append the data from the webscrape/api call to their respected arrays (List[object])
# Going forward, "3" != "Yesterday" so we append that data
# Going forward, "3" != "2" so we append that data
# Going forward, "3" != "3" equates to false, therefore, the loop breaks and it returns the resulting data

# So in this case we would have to create a simple conditional that compares how many days we want to whatever time stamp is given in each of those webscraping/api request functions!

# Of course, we already check for duplicates so that won't need to be a worry


def extract_command_value() -> str:
    parser = argparse.ArgumentParser(
        description="Custom command for specifying days for fetching jobs."
    )

    # Add an argument (the custom command) along with the help functionality to see what the command does
    parser.add_argument(
        "--days-needed", type=int, help="The number of days needed to fetch jobs."
    )

    # Parse the argument and insert into a variable
    arguments = parser.parse_args()

    # Create a new variable to access the --days-needed command
    days_needed_variable = arguments.days_needed

    # Return that variable that holds the --days-needed command

    # TO DO - Accessing the value that we input in
    return days_needed_variable


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

    command_line_value = extract_command_value()  # Extracts command-line value

    for elem in response["hits"]:
        time = elem["formatted_relative_time"]

        numeric = re.search(r"\d+", time)
        formatted_time_integer = int(numeric.group()) if numeric else 0

        if len(rapid_jobs) <= 5 and int(command_line_value) >= formatted_time_integer:
            job = {}
            job["_company"] = elem["company_name"]
            job["_title"] = elem["title"]
            job["_location"] = elem["location"]
            job["_link"] = f'https://www.indeed.com/viewjob?jk={elem["id"]}&locality=us'

        # print(elem)

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

    date_div_post = parse_content.find_all(
        "time",
        class_="job-search-card__listdate",
    )  # Recieves all the job posting dates

    command_line_value = extract_command_value()  # Extracts command-line value

    linked_in_jobs = []

    for elem, date in zip(div_post, date_div_post):
        # If the value of date.text.strip() has the word "days" in it, we access the number, and compare it with the
        # value of the command line

        if "days" in date.text.strip():
            numeric = re.search(r"\d+", date.text.strip())
            formatted_time_integer = int(numeric.group()) if numeric else 0

            if (
                len(linked_in_jobs) <= 5
                and int(command_line_value) >= formatted_time_integer
            ):
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
                job["_link"] = elem.find("a", class_="base-card__full-link")[
                    "href"
                ].split("?")[0]

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

    cursor.execute("SELECT * FROM jobs WHERE _processed = 0 LIMIT 10")
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
    number_identifier = 1
    for data_block in data_results:
        _company = data_block["_company"]
        _title = data_block["_title"]
        _location = data_block["_location"]
        _link = data_block["_link"]

        formatted_string += f"\n**{number_identifier}. [{_company}]({_link})** is **NOW** hiring for **{_title}** @{_location}! \n\n"
        number_identifier += 1

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
    payload = {
        "content": " # ✨ :capyshock: NEW JOB POSTINGS BELOW! :capycool:✨✨ ",
        "tts": False,
        "embeds": [
            {
                "title": f"> Job Postings for {date.today()}\n\n",
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


# -----------------EXECUTE FUNCTIONS-----------------


# rapid_data = rapid_response()
# linkedin_data = linkedin_response()

# ingest_opportunities(rapid_data)
# ingest_opportunities(linkedin_data)

# Resetting processed status for testing purposes only
reset_processed_status()

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

# list_all_opportunities()
