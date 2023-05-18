import requests
import os
import discord
from typing import List
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import sqlite3

# For using my .ENV files
load_dotenv()


# -------------------FOR SQLLITE----------------------------

# https://docs.python.org/3/library/sqlite3.html
# https://www.blog.pythonlibrary.org/2021/09/30/sqlite/#:~:text=Here%20is%20how%20you%20would%20create%20a%20SQLite,the%20sqlite3%20module%20will%20create%20an%20empty%20database.


def create():
    # Creates the DB. Only needs to be called once.

    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS jobs(_company TEXT, _title TEXT, _location TEXT, _link TEXT, _processed BOOLEAN DEFAULT 0)"""
    )

    connection.commit()
    connection.close()


def ingest_opportunities(job_data):
    # Inserts opportunities if and only if they do not already exist

    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    for job in job_data:
        cursor.execute(
            "SELECT COUNT(*) FROM jobs WHERE _company = ?, AND _title = ?, AND _location = ?",
            (job["_company"], job["_title"], job["_location"]),
        )
        counter = cursor.fetchone()[0]

        # https://pynative.com/python-cursor-fetchall-fetchmany-fetchone-to-read-rows-from-table/

        if counter == 0:  # The Job Exists if the counter is 0
            cursor.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?)",
                (job["_company"], job["_title"], job["_location"], job["_link"], False),
            )
        else:
            continue

    connection.commit()
    connection.close()


# -------------------FOR REDDIT----------------------------


# TO-DO: Fix this up to add the company and the location
def reddit_scrape() -> List[object]:
    # Web Scrapping Tools
    software_engineer_url = os.getenv("SOFTWARE_ENGINEER_URL")

    response = requests.get(software_engineer_url)

    content = response.text

    parse_content = BeautifulSoup(content, "html.parser")

    div_post = parse_content.find_all("div", class_="_1poyrkZ7g36PawDueRza-J")

    reddit_jobs = []

    for element in div_post:
        header_title = element.find("h3", class_="_eYtD2XCVieq6emjKBH3m")
        link_job = element.find("a", class_="_3t5uN8xUmg0TOwRCOGQEcU")

        job = {}

        if link_job is not None:
            job["_title"] = header_title.text
            job["_link"] = link_job.get("href")

            reddit_jobs.append(job)

    return reddit_jobs


# -------------------FOR RAPIDAPI----------------------------


def rapid_response() -> List[object]:
    url = "https://indeed12.p.rapidapi.com/jobs/search?locality=us&query=software+engineer&location=Fullerton&formatted_relative_time=today&page_id=1"

    rapid_api_key = os.getenv("RAPID_API_KEY")
    rapid_api_host = os.getenv("RAPID_API_HOST")

    headers = {
        "X-RapidAPI-Key": rapid_api_key,
        "X-RapidAPI-Host": rapid_api_host,
    }

    rapid_jobs = []
    response = requests.get(url, headers=headers).json()

    for elem in response["hits"]:
        job = {}
        job["_company"] = elem["company_name"]
        job["_title"] = elem["title"]
        job["_location"] = elem["location"]
        job["_link"] = f'https://www.indeed.com/viewjob?jk={elem["id"]}&locality=us'

        rapid_jobs.append(job)

    return rapid_jobs


# -------------------FOR INDEED API----------------------------


# -------------------FOR LINKEDIN----------------------------


def indeed_response() -> List[object]:
    url = os.getenv("LINKEDIN_URL")

    response = requests.get(url)

    content = response.text

    parse_content = BeautifulSoup(content, "html.parser")

    div_post = parse_content.find_all(
        "div",
        class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
    )

    indeed_jobs = []

    for elem in div_post:
        job = {}
        job["_company"] = elem.find(
            "h4", class_="base-search-card__subtitle"
        ).text.strip()
        job["_title"] = elem.find("h3", class_="base-search-card__title").text.strip()
        job["_location"] = elem.find(
            "span", class_="job-search-card__location"
        ).text.strip()
        job["_link"] = elem.find("a", class_="base-card__full-link")["href"]

        indeed_jobs.append(job)

    return indeed_jobs


# -------------------FOR HELPER FUNCTIONS (possible in class)----------------------------

# List opportunities shows all the opportunities that have NOT been posted yet


def list_opportunities() -> List[object]:
    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM jobs")
    rows = cursor.fetchall()

    # Printing out for debugging purposes
    for row in rows:
        _company = row[0]
        _title = row[1]
        _location = row[2]
        _link = row[3]
        _processed = row[4]

        if _processed == False:
            print("Company:", _company)
            print("Title:", _title)
            print("Location:", _location)
            print("Link:", _link)
            print("Processed:", _processed)
            print(" ")

    connection.close()

    return rows
    # TO-DO: RETURN THE JOBS THAT HAVENT BEEN POSTED


# -------------------FOR DISCORD BOT----------------------------


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
discord_token = os.getenv("DISCORD_TOKEN")

# TO DO - Ask Ethan about the web hook thingy kabob
# webhook = /HIDDEN/


async def execute_opportunities_webhook():
    channel_id = os.getenv("DISCORD_CHANNEL_ID")

    channel = client.get_channel(channel_id)
    await channel.send("testing...")

    data_results = list_opportunities()

    for element in data_results:
        company = element[0]
        title = element[1]
        location = element[2]
        link = element[3]
        status = element[4]

        # Checking to see if the PROCESSED status is 0, and if so, means false.
        if status == 0:
            await channel.send(
                f"NEW JOB! {company} is hiring for {title} at {location}!!! Link: {link}"
            )

        connection = sqlite3.connect("jobs.db")
        cursor = connection.cursor()

        # Updating the PROCESSED status to 1, which means its already been posted.
        cursor.execute(
            "UPDATE jobs SET status = ? WHERE company = ? AND title = ?",
            (1, company, title),
        )

        connection.commit()
        connection.close()


@client.event
async def on_ready():
    await execute_opportunities_webhook()


client.run(discord_token)


# -----------------TESTING WHAT I HAVE SO FAR-----------------

# TO-DO: Create a limit for the jobs, because the discord bot currently spammed me 32 jobs in one sitting lol


# Lines 254 and 255 web scrap/send an api request for the jobs!
# indeed_response = indeed_response()
# rapid_response = rapid_response()

# Lines 258 and 259 actually place all that data into the DB
# ingest_opportunities(indeed_response)
# ingest_opportunities(rapid_response)

# Just prints out the jobs in general
# list_opportunities()
