from dataclasses import dataclass
from dotenv import load_dotenv
from typing import List
import utility.db as db
from enum import Enum
import os

load_dotenv()


class OpportunityType(Enum):
    """Enum holding the type of unique opportunity"""

    FULL_TIME = "full_time"
    INTERNSHIP = "internship"
    CONFERENCE = "conference"
    SCHOLARHSHIP = "scholarship"


@dataclass
class Opportunity:
    """Struct to hold data for an opportunity"""

    company: str
    title: str
    location: str
    link: str
    processed: bool
    type: OpportunityType


table_name = os.getenv("DB_TABLE")


def ingest_opportunities(job_data: List[Opportunity]) -> None:
    """Inserts opportunities if and only if they do not already exist"""

    supabase = db.create_supabase_client()
    for job in job_data:
        response = (
            supabase.table(table_name)
            .select("company, title, location, type")
            .eq(
                {
                    "company": job.company,
                    "title": job.title,
                    "location": job.location,
                    "type": job.type,
                }
            )
            .execute()
        )
        if not response.data:
            response = (
                supabase.table(table_name)
                .insert(
                    {
                        "company": job.company,
                        "title": job.title,
                        "location": job.location,
                        "type": job.type,
                    }
                )
                .execute()
            )


def list_opportunities(
    debug: bool,
    opp_type: str,
    filtered=False,
) -> List[Opportunity]:
    """Lists all oppportunities in DB as well as returns them"""

    supabase = db.create_supabase_client()
    if filtered:
        response = (
            supabase.table(table_name)
            .select("*")
            .match({"processed": 0, "type": opp_type})
            .limit(15)
            .execute()
        )
    else:
        response = supabase.table(table_name).select("*")
    return read_all_opportunities(response.data, debug)


def read_all_opportunities(rows, debug_tool: bool) -> List[Opportunity]:
    """Helper function designed to return filtered or unfiltered opportunities"""
    opportunities = []

    for row in rows:
        company, title, location, link, processed, type = row

        if debug_tool:
            print("Company:", company)
            print("Title:", title)
            print("Location:", location)
            print("Link:", link)
            print("Processed:", processed)
            print("Type: ", type)
            print(" ")

        opportunity = Opportunity(company, title, location, link, processed, type)

        opportunities.append(opportunity)

    return opportunities


def update_opportunities_status(data_results: List[Opportunity]) -> None:
    """Updates the status of the jobs to processed = 1 after it's been sent by the discord bot"""

    supabase = db.create_supabase_client()
    for data_block in data_results:
        supabase.table(table_name).update({"processed": 1}).match(
            {
                "company": data_block.company,
                "title": data_block.title,
                "location": data_block.location,
            }
        ).execute()


def format_opportunities(data_results: List[Opportunity], formatted_text: str) -> str:
    """Receives data from list_filtered_opporunities() and returns a single string message"""

    formatted_string = ""

    for data_block in data_results:
        company = data_block.company
        title = data_block.title
        location = data_block.location
        link = data_block.link

        formatted_string += formatted_text.format(
            company=company, title=title, location=location, link=link
        )
        formatted_string += "\n"

    return formatted_string
