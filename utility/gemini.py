from time import sleep
import os
import utility.utils as utils
from dotenv import load_dotenv
import json
from google import genai
from google.genai import types

from utility.opportunity import Opportunity

load_dotenv()
utils.verify_set_env_variables()


MAX_RETRY = 5  # Max number of retrys
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def parse_gpt_values(gpt_response: str) -> list[bool]:
    """Parse a JSON array of booleans from Gemini's response."""
    return json.loads(gpt_response.lower())


def filter_out_opportunities(
    list_of_opps: list[Opportunity], gpt_response: list[bool]
) -> list[Opportunity]:
    """Helper function for gpt_job_analyzer() to filter the data"""

    structured_opps = [
        opp for opp, response in zip(list_of_opps, gpt_response) if response
    ]

    print(
        f"Length after GPT analyzed the {list_of_opps[0].type_of_opportunity}: {len(structured_opps)}"
    )
    return structured_opps


def get_parsed_values(prompt: str) -> list[bool]:
    """Function which returns parsed values if the opportunity mathces with the clubs values"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            candidate_count=1,
            top_k=100,
            top_p=0.95,
            max_output_tokens=3072,
            response_mime_type="application/json",
        ),
    )

    if response.text is None:
        raise ValueError("Gemini was not able to return a response")

    return parse_gpt_values(response.text)


def gpt_job_analyze(list_of_opps: list[Opportunity], prompt: str) -> list[Opportunity]:
    """Analyzes each job opportunity before being inserted into the DB"""

    print(
        f"The type '{list_of_opps[0].type_of_opportunity}' original length before filtering: {len(list_of_opps)}"
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

            if len(parsed_values) == 0:
                continue
            break
        except (
            json.decoder.JSONDecodeError
        ):  # The type of error that would be received is type JSON
            sleep(0.5)

    print(f" Below are the parsed values from GPT - {parsed_values}")

    return filter_out_opportunities(
        list_of_opps, parsed_values
    )  # Returns filtered out opportunities
