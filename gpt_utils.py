from typing import List
import json
import openai
import os
from opportunity import Opportunity
from time import sleep


MAX_RETRY = 15  # Max number of retrys for the gpt_job_analyzer() function

openai.api_key = os.getenv("GPT_API_KEY")


def parse_gpt_values(gpt_response) -> List[bool]:
    """Helper function to parse the gpt response from a str -> List[bool]"""

    return json.loads(gpt_response)


def filter_out_opportunities(list_of_opps, gpt_response) -> List[Opportunity]:
    """Helper function for gpt_job_analyzer() to filter the data"""
    structured_opps = [
        opp for opp, response in zip(list_of_opps, gpt_response) if response
    ]

    print(f"Length after GPT analyzed the jobs: {len(structured_opps)}")
    return structured_opps


def get_parsed_values(prompt) -> List[bool]:
    """Function which returns parsed values if the opportunity mathces with the clubs values"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a job analyzer for college students.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    print(response.choices[0].message["content"])
    parsed_values = parse_gpt_values(response.choices[0].message["content"])

    return parsed_values


def gpt_job_analyzer(list_of_opps) -> List[Opportunity]:
    """Analyzes each job opportunity before being inserted into the DB"""

    print(f"The jobs original length before filtering: {len(list_of_opps)}")

    prompt = "Your role is to assess job opportunities for college students in the tech industry, particularly those pursuing Computer Science majors and seeking entry-level positions. To aid in this decision-making process, please provide a list of booleans (True/False) for each job that aligns with our goal of offering entry-level tech-related positions to college students. Please state the list of booleans directly as minified JSON array of boolean values, without any additional text or comments."

    for opp in list_of_opps:
        prompt += f"\nCompany: {opp._company}"
        prompt += f"\nTitle: {opp._title}"
        prompt += f"\nLocation: {opp._location}"
        prompt += "\n"

    parsed_values = []
    for _ in range(MAX_RETRY):  # Keep looping until a valid prompt is recieved
        try:
            parsed_values = get_parsed_values(prompt)
            break
        except (
            json.decoder.JSONDecodeError
        ):  # The type of error that would be recieved is type JSON
            sleep(0.5)

    print(f" Below are the parsed values from GPT\n {parsed_values}")
    print(parsed_values)  # For debugging purposes

    return filter_out_opportunities(
        list_of_opps, parsed_values
    )  # Returns filtered out opportunities
