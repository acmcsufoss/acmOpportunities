import requests
import os
import json
import asyncio
from datetime import date
import utility.utils as ut
import utility.db as db
import utility.opportunity as opps
from dotenv import load_dotenv
from utility.scrape import (
    request_github_internship24_data,
    request_linkedin_data,
    request_linkedin_internship24_data,
)
from utility.palm import gpt_job_analyze


# Load and determine if all env variables are set
load_dotenv()
ut.verify_set_env_variables()


async def execute_opportunities_webhook(
    webhook_url: str, job_message: str, internship_message: str
):
    """
    Executes the message which receives the formatted message
    from the format_opportunities() function as well as the webhook
    url for the respected discord channel
    """

    # Create a dictionary payload for the message content
    payload = {
        "content": "# ✨ NEW OPPORTUNITY POSTINGS BELOW! ✨",
        "tts": False,
        "embeds": [
            {
                "title": f"✧･ﾟ: *✧･ﾟ:* 🎀 {date.today()} 🎀 ✧･ﾟ: *✧･ﾟ:*｡",
                "color": 0xFFFFFF,
            },
        ],
    }

    if job_message:
        payload["embeds"].append(
            {
                "title": "¸„.-•~¹°”ˆ˜¨ JOB OPPORTUNITIES ¨˜ˆ”°¹~•-.„¸",
                "description": job_message,
                "color": 0x05A3FF,
            },
        )

    if internship_message:
        payload["embeds"].append(
            {
                "title": " ¸„.-•~¹°”ˆ˜¨ INTERNSHIP OPPORTUNITIES ¨˜ˆ”°¹~•-.„¸",
                "description": internship_message,
                "color": 0x05A3FF,
            },
        )

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
    # Creates table in database
    with_create_table_command = ut.extract_command_value().create
    if with_create_table_command:
        TABLE_NAME = os.getenv("DB_TABLE")

        db.create(TABLE_NAME)

        print(f"Sucessfully created {TABLE_NAME}!")
        exit()  # Exit the main function to avoid calling other functions

    file_paths = [os.getenv("MESSAGE_PATH"), os.getenv("PROMPTS_PATH")]
    customized_object = ut.user_customization(file_paths)

    # Determines the customized prompts for PaLM
    prompt_object = ut.determine_prompts(customized_object["customized_prompts"])

    # Determines the customized message for the webhook
    finalized_message = ut.determine_customized_message(
        customized_object["customized_message"]
    )

    # Consolidates all job-related opportunities into a comprehensive List[Opportunity], eliminating repetitive calls to the LLM SERVER.
    job_opps = ut.merge_all_opportunity_data(request_linkedin_data())

    filtered_job_opps = gpt_job_analyze(
        job_opps,
        prompt_object["full_time"],
    )
    opps.ingest_opportunities(filtered_job_opps)

    # Consolidates all job-related opportunities into a comprehensive List[Opportunity], eliminating repetitive calls to the LLM SERVER.
    internship_opps = ut.merge_all_opportunity_data(
        request_linkedin_internship24_data(), request_github_internship24_data()
    )

    filtered_internship_opps = gpt_job_analyze(
        internship_opps,
        prompt_object["internship"],
    )
    opps.ingest_opportunities(filtered_internship_opps)

    # To test the code without consuming API requests, call reset_processed_status().
    # This function efficiently resets the processed status of 5 job postings by setting them to _processed = 0.
    # By doing so, developers can run tests without wasting valuable API resources.
    # To do so, please comment the function calls above this comment.
    # After, please uncomment the following line of code:

    # db.reset_processed_status()

    internship_data_results = opps.list_opportunities(True, "internship", filtered=True)
    job_data_results = opps.list_opportunities(True, "full_time", filtered=True)

    internship_formatted_message = opps.format_opportunities(
        internship_data_results, finalized_message
    )
    job_formatted_message = opps.format_opportunities(
        job_data_results, finalized_message
    )

    discord_webhook = os.getenv("DISCORD_WEBHOOK")

    await execute_opportunities_webhook(
        discord_webhook, job_formatted_message, internship_formatted_message
    )

    opps.update_opportunities_status(job_data_results)
    opps.update_opportunities_status(internship_data_results)


if __name__ == "__main__":
    asyncio.run(main())
