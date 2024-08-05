from dataclasses import dataclass
from dotenv import load_dotenv
from typing import List
import utility.db as db
from enum import Enum
import uuid
from datetime import datetime
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

    id: any
    company: str
    title: str
    location: str
    link: str
    processed: bool
    type_of_opportunity: OpportunityType


TABLE_NAME = os.getenv("DB_TABLE_NAME")


def ingest_opportunities(job_data: List[Opportunity]) -> None:
    """Inserts opportunities if and only if they do not already exist"""

    supabase = db.SupabaseConnection().CLIENT
    for job in job_data:

        response = (
            supabase.table(TABLE_NAME)
            .select("id, company, title, location, link, processed, type")
            .eq("company", job.company)
            .eq("title", job.title)
            .eq("location", job.location)
            .eq("link", job.link)
            .eq("type", job.type_of_opportunity)
            .execute()
        )

        if not response.data:
            request = supabase.table(TABLE_NAME).insert(
                {
                    "id": str(uuid.uuid4()),
                    "company": job.company,
                    "title": job.title,
                    "location": job.location,
                    "link": job.link,
                    "processed": job.processed,
                    "type": job.type_of_opportunity,
                }
            )

            response = request.execute()


def list_opportunities(
    debug: bool,
    opp_type: str,
    filtered=False,
) -> List[Opportunity]:
    """Lists all oppportunities in DB as well as returns them"""

    supabase = db.SupabaseConnection().CLIENT

    if filtered:
        response = (
            supabase.table(TABLE_NAME)
            .select("*")
            .match({"processed": False, "type": opp_type})
            .limit(15)
            .execute()
        )
    else:
        response = supabase.table(TABLE_NAME).select("*")

    return read_all_opportunities(response.data, debug)


def read_all_opportunities(rows, debug_tool: bool) -> List[Opportunity]:
    """Helper function designed to return filtered or unfiltered opportunities"""
    opportunities = []

    for row in rows:
        if debug_tool:
            print("Id:", row.get("id"))
            print("Company:", row.get("company"))
            print("Title:", row.get("title"))
            print("Location:", row.get("location"))
            print("Link:", row.get("link"))
            print("Processed:", row.get("processed"))
            print("Type: ", row.get("type"))
            print(" ")

        opportunity = Opportunity(
            row.get("id"),
            row.get("company"),
            row.get("title"),
            row.get("location"),
            row.get("link"),
            row.get("processed"),
            row.get("type"),
        )

        opportunities.append(opportunity)

    return opportunities


def update_opportunities_status(data_results: List[Opportunity]) -> None:
    """Updates the status of the jobs to processed = 1 after it's been sent by the discord bot"""

    supabase = db.SupabaseConnection().CLIENT
    for data_block in data_results:
        supabase.table(TABLE_NAME).update({"processed": 1}).match(
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
