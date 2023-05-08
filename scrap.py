import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv


software_engineer_url = "https://www.reddit.com/r/SoftwareEngineerJobs/"
response = requests.get(software_engineer_url)

content = response.text

parse_content = BeautifulSoup(content, "html.parser")

header_post = parse_content.find_all(class_="_eYtD2XCVieq6emjKBH3m")
link_to_job = parse_content.find_all(class_="_3t5uN8xUmg0TOwRCOGQEcU")
entire_job_info = parse_content.find_all(class_="_3DYfYn_cczg1wj_a3hhyV6")


def JobLink():
    job_links = []
    for element in link_to_job:
        print(element["href"])
        job_links.append(element["href"])

    return job_links


def HeaderPost():
    header_titles = []
    for element in header_post:
        print(element.text)
        header_titles.append(element.text)

    return header_titles


def ReturnJobObject():
    object_variable = {job_link: JobLink(), header_post: HeaderPost()}

    return object_variable


def EntireInfoReMotive():
    for element in entire_job_info:
        print(element.text)


# TESTING THIS
HeaderPost()
JobLink()
