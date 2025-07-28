import os
from pathlib import Path
import json
from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables or .env file")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

QUESTIONS_PATH = "survey_questions.json"

def init_db():
    """Initialize database tables in Supabase. This should be run once to create the tables."""
    # Note: In Supabase, tables are typically created through the dashboard or migrations
    # This function is kept for compatibility but tables should be created manually in Supabase
    print("Database tables should be created in Supabase dashboard")
    print("Required tables: campaign, question, call, answer")
    
    # You can also create tables programmatically if needed:
    # This would require additional setup and permissions

def create_campaign(name, description=None, start_date=None, end_date=None,
                    intro_prompt=None, purpose_explanation=None, greeting=None, closing=None):
    """Create a new campaign in Supabase."""
    try:
        data = {
            "name": name,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "intro_prompt": intro_prompt,
            "purpose_explanation": purpose_explanation,
            "greeting": greeting,
            "closing": closing
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        result = supabase.table("campaign").insert(data).execute()
        
        if result.data:
            campaign_id = result.data[0]["id"]
            print(f"Created campaign with id: {campaign_id}")
            return campaign_id
        else:
            raise Exception("Failed to create campaign")
            
    except Exception as e:
        print(f"Error creating campaign: {e}")
        raise

def add_question(campaign_id, question_text, question_order):
    """Add a question to a campaign in Supabase."""
    try:
        data = {
            "campaign_id": campaign_id,
            "question_text": question_text,
            "question_order": question_order
        }
        
        result = supabase.table("question").insert(data).execute()
        
        if result.data:
            question_id = result.data[0]["id"]
            print(f"Added question {question_order} with id: {question_id}")
            return question_id
        else:
            raise Exception("Failed to add question")
            
    except Exception as e:
        print(f"Error adding question: {e}")
        raise

def create_campaign_room_mapping(campaign_id, room_pattern, is_active=True):
    """Create a new campaign room mapping in Supabase."""
    try:
        data = {
            "campaign_id": campaign_id,
            "room_pattern": room_pattern,
            "is_active": is_active
        }
        
        result = supabase.table("campaign_room_mapping").insert(data).execute()
        
        if result.data:
            mapping_id = result.data[0]["id"]
            print(f"Created campaign room mapping with id: {mapping_id}")
            return mapping_id
        else:
            raise Exception("Failed to create campaign room mapping")
            
    except Exception as e:
        print(f"Error creating campaign room mapping: {e}")
        raise

def get_campaign_by_room_name(room_name):
    """Get campaign for a specific room name by matching against room patterns."""
    try:
        # Get all active campaign room mappings
        result = supabase.table("campaign_room_mapping").select("*").eq("is_active", True).execute()
        
        if not result.data:
            # Fallback to most recent campaign if no mappings found
            return get_campaign_from_db()
        
        # Find the first matching pattern
        for mapping in result.data:
            pattern = mapping["room_pattern"]
            if room_name.startswith(pattern):
                campaign_id = mapping["campaign_id"]
                return get_campaign_by_id(campaign_id)
        
        # If no pattern matches, fallback to most recent campaign
        print(f"No campaign mapping found for room: {room_name}, using fallback")
        return get_campaign_from_db()
            
    except Exception as e:
        print(f"Error getting campaign by room name: {e}")
        # Fallback to most recent campaign
        return get_campaign_from_db()

def get_campaign_by_id(campaign_id):
    """Get a specific campaign by ID from Supabase."""
    try:
        result = supabase.table("campaign").select("*").eq("id", campaign_id).execute()
        
        if result.data:
            campaign = result.data[0]
            return {
                "id": campaign["id"],
                "name": campaign["name"],
                "description": campaign["description"],
                "intro_prompt": campaign["intro_prompt"],
                "purpose_explanation": campaign["purpose_explanation"],
                "greeting": campaign["greeting"],
                "closing": campaign["closing"],
            }
        else:
            raise Exception(f"No campaign found with id: {campaign_id}")
            
    except Exception as e:
        print(f"Error getting campaign by id: {e}")
        raise

def record_call(phone_number, campaign_id, room_name, call_timestamp=None, s3_recording_url=None):
    """Record a call in Supabase."""
    try:
        data = {
            "phone_number": phone_number,
            "campaign_id": campaign_id,
            "room_name": room_name,
            "s3_recording_url": s3_recording_url
        }
        
        # Add timestamp if provided, otherwise Supabase will use default
        if call_timestamp:
            data["call_timestamp"] = call_timestamp
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        result = supabase.table("call").insert(data).execute()
        
        if result.data:
            call_id = result.data[0]["id"]
            print(f"Recorded call with id: {call_id}")
            return call_id
        else:
            raise Exception("Failed to record call")
            
    except Exception as e:
        print(f"Error recording call: {e}")
        raise

def record_answer(call_id, question_id, answer_text, answered_at=None):
    """Record an answer in Supabase."""
    try:
        # First, check if an answer already exists for this call and question
        existing_result = supabase.table("answer").select("id").eq("call_id", call_id).eq("question_id", question_id).execute()
        
        if existing_result.data:
            # Answer already exists, update it instead of inserting
            answer_id = existing_result.data[0]["id"]
            update_data = {"answer_text": answer_text}
            if answered_at:
                update_data["answered_at"] = answered_at
            
            result = supabase.table("answer").update(update_data).eq("id", answer_id).execute()
            
            if result.data:
                print(f"Updated existing answer with id: {answer_id}")
                return answer_id
            else:
                raise Exception("Failed to update existing answer")
        else:
            # No existing answer, insert new one
            data = {
                "call_id": call_id,
                "question_id": question_id,
                "answer_text": answer_text
            }
            
            # Add timestamp if provided, otherwise Supabase will use default
            if answered_at:
                data["answered_at"] = answered_at
            
            result = supabase.table("answer").insert(data).execute()
            
            if result.data:
                answer_id = result.data[0]["id"]
                print(f"Recorded new answer with id: {answer_id}")
                return answer_id
            else:
                raise Exception("Failed to record answer")
            
    except Exception as e:
        print(f"Error recording answer: {e}")
        raise

def get_campaign_from_db():
    """Get the most recent campaign from Supabase."""
    try:
        result = supabase.table("campaign").select("*").order("id", desc=True).limit(1).execute()
        
        if result.data:
            campaign = result.data[0]
            return {
                "id": campaign["id"],
                "name": campaign["name"],
                "description": campaign["description"],
                "intro_prompt": campaign["intro_prompt"],
                "purpose_explanation": campaign["purpose_explanation"],
                "greeting": campaign["greeting"],
                "closing": campaign["closing"],
            }
        else:
            raise Exception("No campaign found in database.")
            
    except Exception as e:
        print(f"Error getting campaign: {e}")
        raise

def get_questions_for_campaign(campaign_id):
    """Get all questions for a campaign from Supabase."""
    try:
        result = supabase.table("question").select("*").eq("campaign_id", campaign_id).order("question_order").execute()
        
        if result.data:
            return [(q["id"], q["question_text"], q["question_order"]) for q in result.data]
        else:
            return []
            
    except Exception as e:
        print(f"Error getting questions: {e}")
        return []

def update_call_s3_url(call_id, s3_recording_url):
    """Update the S3 recording URL for a call."""
    try:
        result = supabase.table("call").update({"s3_recording_url": s3_recording_url}).eq("id", call_id).execute()
        
        if result.data:
            print(f"Updated call {call_id} with S3 recording URL: {s3_recording_url}")
            return True
        else:
            print(f"No call found with id {call_id}")
            return False
            
    except Exception as e:
        print(f"Error updating call S3 URL: {e}")
        return False

def get_existing_answers_for_call(call_id):
    """Get existing answers for a call to avoid duplicates."""
    try:
        result = supabase.table("answer").select("question_id").eq("call_id", call_id).execute()
        if result.data:
            return [answer["question_id"] for answer in result.data]
        else:
            return []
    except Exception as e:
        print(f"Error getting existing answers: {e}")
        return []

# Example usage
if __name__ == "__main__":
    init_db()
    # Create a campaign
    campaign_id = create_campaign(
        name="InnoVet-AMR 2024",
        description="Survey on climate change, AMR, and animal health.",
        intro_prompt="You are the automated survey agent for the InnoVet-AMR initiative.",
        purpose_explanation="Thank you for taking part in our InnoVet-AMR survey.",
        greeting="Hello, welcome to our survey.",
        closing="Thank you for completing this survey. We value your input."
    )

    # Add all questions from survey_questions.json
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)
    for q_num in sorted(questions, key=lambda x: int(x)):
        q_text = questions[q_num]
        qid = add_question(campaign_id, q_text, int(q_num))
