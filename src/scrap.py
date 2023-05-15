import requests
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# -------------------FOR REDDIT----------------------------


def RedditScrap():
    # WebScrapping Tools
    software_engineer_url = os.getenv("SOFTWARE_ENGINEER_URL")

    response = requests.get(software_engineer_url)

    content = response.text

    parse_content = BeautifulSoup(content, "html.parser")

    div_post = parse_content.find_all(
        "div",
        class_="_1poyrkZ7g36PawDueRza-J",
    )

    # WebScrapping Action soup.findAll('a', attrs={'href': re.compile("^http://")})

    reddit_jobs = []

    for element in div_post:
        header_title = element.find("h3", class_="_eYtD2XCVieq6emjKBH3m")
        link_job = element.find("a", class_="_3t5uN8xUmg0TOwRCOGQEcU")

        if link_job is not None:
            job = {"_title": header_title.text, "_link": link_job.get("href")}
            reddit_jobs.append(job)

    if len(reddit_jobs) != 0:
        for elem in reddit_jobs:
            print(elem["_title"], " : ", elem["_link"])
    else:
        print("There are no elements in this vector. Please try again")

    return reddit_jobs


# -------------------FOR RAPIDAPI----------------------------


def RapidResponse():
    url = "https://indeed12.p.rapidapi.com/jobs/search?locality=us&query=software&location=Fullerton&formatted_relative_time=today&page_id=1"

    rapid_api_key = os.getenv("RAPID_API_KEY")

    headers = {
        "X-RapidAPI-Key": rapid_api_key,
        "X-RapidAPI-Host": "indeed12.p.rapidapi.com",
    }

    rapid_jobs = []
    response = requests.get(url, headers=headers).json()

    for elem in response["hits"]:
        job = {}
        job["_company"] = elem["company_name"]
        job["_title"] = elem["title"]
        job["_location"] = elem["location"]
        job["_link"] = f'https://www.indeed.com/viewjob?jk={elem["id"]}&locality=us'
        # f means a formatted string literal in python
        # job.append(
        #     {
        #         "_company": elem.company_name,
        #         "_title": elem.title,
        #         "_location": elem.location,
        #         "_link": "https://www.indeed.com/viewjob?jk={elem.id}&locality=us",
        #     }
        # )

        rapid_jobs.append(job)

    for elem in rapid_jobs:
        print(elem)

    return rapid_jobs


# -------------------FOR INDEED API----------------------------


# -------------------FOR HELPER FUNCTIONS (possible in class)----------------------------


# -------------------FOR SQLLITE----------------------------


# -------------------FOR DISCORD BOT----------------------------


# -----------------TESTING WHAT I HAVE SO FAR-----------------
RedditScrap()
RapidResponse()
