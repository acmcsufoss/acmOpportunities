from typing import List
import json
import openai
import os
from time import sleep
import pprint
import google.generativeai as palm

MAX_RETRY = 5  # Max number of retrys for the gpt_job_analyzer() function

openai.api_key = os.getenv("GPT_API_KEY")

PALM_API_KEY = os.getenv("PALM_API_KEY")
palm.configure(api_key=PALM_API_KEY)


def find_model() -> any:
    """Returns the model in use"""

    models = [
        m
        for m in palm.list_models()
        if "generateText" in m.supported_generation_methods
    ]

    model = models[0].name

    return model


def parse_gpt_values(gpt_response) -> List[bool]:
    """Helper function to parse the gpt response from a str -> List[bool]"""
    return json.loads(gpt_response.lower())


def filter_out_opportunities(list_of_opps, gpt_response):
    """Helper function for gpt_job_analyzer() to filter the data"""
    structured_opps = [
        opp for opp, response in zip(list_of_opps, gpt_response) if response
    ]

    print(structured_opps)
    print(f"Length after GPT analyzed the jobs: {len(structured_opps)}")
    return structured_opps


def get_parsed_values(prompt) -> List[bool]:
    """Function which returns parsed values if the opportunity mathces with the clubs values"""

    model = find_model()

    completion = palm.generate_text(
        model=model, prompt=prompt, temperature=0, max_output_tokens=500
    )

    parsed_values = parse_gpt_values(completion.result)
    return parsed_values


def gpt_job_analyzer(list_of_opps):
    """Analyzes each job opportunity before being inserted into the DB"""

    print(f"The jobs original length before filtering: {len(list_of_opps)}")

    prompt = """
        Your role is to assess job opportunities
        for college students in the tech industry,
        particularly those pursuing Computer Science
        majors and seeking entry-level positions.
        To aid in this decision-making process, please
        respond a minified JSON list of booleans (True/False)
        for each job that aligns with our goal of offering
        entry-level tech-related positions to college
        students. Please include the List[bool] only.
        """

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
