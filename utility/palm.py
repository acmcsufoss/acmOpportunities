import google.generativeai as palm
from time import sleep
import os
import utility.utils as utils
from dotenv import load_dotenv
from typing import List
import json
from utility.opportunity import Opportunity

load_dotenv()
utils.verify_set_env_variables()


MAX_RETRY = 5  # Max number of retrys
palm.configure(api_key=os.getenv("PALM_API_KEY"))


def current_model_inuse() -> any:
    """Returns the model in use"""

    models = [
        m
        for m in palm.list_models()
        if "generateText" in m.supported_generation_methods
    ]

    model = models[0].name

    return model


def parse_gpt_values(gpt_response: str) -> List[bool]:
    """Helper function to parse the gpt response from a str -> List[bool]"""

    response: List[bool]

    for _ in range(MAX_RETRY):
        try:
            response = json.loads(gpt_response.lower())
            break
        except AttributeError:
            sleep(0.5)

    return response


def filter_out_opportunities(
    list_of_opps: List[Opportunity], gpt_response: List[bool]
) -> List[Opportunity]:
    """Helper function for gpt_job_analyzer() to filter the data"""

    structured_opps = [
        opp for opp, response in zip(list_of_opps, gpt_response) if response
    ]

    print(
        f"Length after GPT analyzed the {list_of_opps[0].type}: {len(structured_opps)}"
    )
    return structured_opps


def get_parsed_values(prompt: str) -> List[bool]:
    """Function which returns parsed values if the opportunity mathces with the clubs values"""

    defaults = {
        "model": "models/text-bison-001",
        "temperature": 0.0,
        "candidate_count": 1,
        "top_k": 100,
        "top_p": 0.95,
        "max_output_tokens": 3072,
        "stop_sequences": [],
        "safety_settings": [
            {"category": "HARM_CATEGORY_DEROGATORY", "threshold": 3},
            {"category": "HARM_CATEGORY_TOXICITY", "threshold": 3},
            {"category": "HARM_CATEGORY_VIOLENCE", "threshold": 3},
            {"category": "HARM_CATEGORY_SEXUAL", "threshold": 3},
            {"category": "HARM_CATEGORY_MEDICAL", "threshold": 3},
            {"category": "HARM_CATEGORY_DANGEROUS", "threshold": 3},
        ],
    }

    completion = palm.generate_text(**defaults, prompt=prompt)

    parsed_values = parse_gpt_values(completion.result)
    return parsed_values


def gpt_job_analyze(list_of_opps: List[Opportunity], prompt: str) -> List[Opportunity]:
    """Analyzes each job opportunity before being inserted into the DB"""

    print(
        f"The type '{list_of_opps[0].type}' original length before filtering: {len(list_of_opps)}"
    )

    for opp in list_of_opps:
        prompt += f"\nCompany: {opp.company}"
        prompt += f"\nTitle: {opp.title}"
        prompt += f"\nLocation: {opp.location}"
        prompt += "\n"

    parsed_values = []
    for _ in range(MAX_RETRY):  # Keep looping until a valid prompt is received
        try:
            parsed_values = get_parsed_values(prompt)
            break
        except (
            json.decoder.JSONDecodeError
        ):  # The type of error that would be received is type JSON
            sleep(0.5)

    print(f" Below are the parsed values from GPT - {parsed_values}")

    return filter_out_opportunities(
        list_of_opps, parsed_values
    )  # Returns filtered out opportunities
