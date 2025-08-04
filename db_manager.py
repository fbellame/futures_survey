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
    print("Required tables: campaign, question, survey_submissions, answer, campaign_room_mapping")
    
    # You can also create tables programmatically if needed:
    # This would require additional setup and permissions

def create_campaign(name, description=None, start_date=None, end_date=None,
                    intro_prompt=None, purpose_explanation=None, greeting=None, closing=None, campaign_type=None):
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
            "closing": closing,
            "campaign_type": campaign_type
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

def get_existing_survey_submission(room_name):
    """Check if a survey submission already exists for a given room name."""
    try:
        result = supabase.table("survey_submissions").select("*").eq("room_name", room_name).execute()
        
        if result.data:
            return result.data[0]  # Return the first (should be only) matching submission
        else:
            return None
            
    except Exception as e:
        print(f"Error checking existing survey submission: {e}")
        return None

# Keep backward compatibility
def get_existing_survey_response(room_name):
    """Check if a survey response already exists for a given room name (legacy wrapper)."""
    return get_existing_survey_submission(room_name)

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
                "campaign_type": campaign.get("campaign_type"),
            }
        else:
            raise Exception(f"No campaign found with id: {campaign_id}")
            
    except Exception as e:
        print(f"Error getting campaign by id: {e}")
        raise

def record_survey_submission(phone_number=None, campaign_id=None, room_name=None, 
                           call_timestamp=None, s3_recording_url=None, 
                           full_name=None, email=None, geography=None, 
                           occupation=None, invitation_token=None):
    """Record a survey submission in Supabase. Check for duplicates first."""
    try:
        # First check if a survey submission already exists for this room
        existing_submission = get_existing_survey_submission(room_name)
        if existing_submission:
            print(f"Survey submission already exists for room {room_name} with id: {existing_submission['id']}")
            return existing_submission['id']
        
        data = {
            "campaign_id": campaign_id,
            "room_name": room_name,
            "phone_number": phone_number,
            "full_name": full_name,
            "email": email,
            "geography": geography,
            "occupation": occupation,
            "invitation_token": invitation_token,
            "s3_recording_url": s3_recording_url
        }
        
        # Add timestamp if provided, otherwise Supabase will use default
        if call_timestamp:
            data["call_timestamp"] = call_timestamp
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        result = supabase.table("survey_submissions").insert(data).execute()
        
        if result.data:
            submission_id = result.data[0]["id"]
            print(f"Recorded survey submission with id: {submission_id}")
            return submission_id
        else:
            raise Exception("Failed to record survey submission")
            
    except Exception as e:
        print(f"Error recording survey submission: {e}")
        raise

def record_survey_response(phone_number, campaign_id, room_name, call_timestamp=None, s3_recording_url=None):
    """Record a survey response in Supabase (legacy wrapper for record_survey_submission)."""
    return record_survey_submission(
        phone_number=phone_number, 
        campaign_id=campaign_id, 
        room_name=room_name, 
        call_timestamp=call_timestamp, 
        s3_recording_url=s3_recording_url
    )

# Keep the old function name for backward compatibility
def record_call(phone_number, campaign_id, room_name, call_timestamp=None, s3_recording_url=None):
    """Record a call in Supabase (legacy wrapper for record_survey_submission)."""
    return record_survey_submission(
        phone_number=phone_number, 
        campaign_id=campaign_id, 
        room_name=room_name, 
        call_timestamp=call_timestamp, 
        s3_recording_url=s3_recording_url
    )

def record_answer(survey_submission_id, question_id, answer_text, answered_at=None):
    """Record an answer in Supabase using survey_submission_id."""
    try:
        # First, check if an answer already exists for this survey submission and question
        existing_result = supabase.table("answer").select("id").eq("survey_submission_id", survey_submission_id).eq("question_id", question_id).execute()
        
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
                "survey_submission_id": survey_submission_id,
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
                "campaign_type": campaign.get("campaign_type"),
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

def update_survey_submission_s3_url(submission_id, s3_recording_url):
    """Update the S3 recording URL for a survey submission."""
    try:
        result = supabase.table("survey_submissions").update({"s3_recording_url": s3_recording_url}).eq("id", submission_id).execute()
        
        if result.data:
            print(f"Updated survey submission {submission_id} with S3 recording URL: {s3_recording_url}")
            return True
        else:
            print(f"No survey submission found with id {submission_id}")
            return False
            
    except Exception as e:
        print(f"Error updating survey submission S3 URL: {e}")
        return False

def update_survey_response_s3_url(survey_response_id, s3_recording_url):
    """Update the S3 recording URL for a survey response (legacy wrapper)."""
    return update_survey_submission_s3_url(survey_response_id, s3_recording_url)

# Keep the old function name for backward compatibility
def update_call_s3_url(call_id, s3_recording_url):
    """Update the S3 recording URL for a call (legacy wrapper)."""
    return update_survey_submission_s3_url(call_id, s3_recording_url)

def get_existing_answers_for_survey_submission(submission_id):
    """Get existing answers for a survey submission to avoid duplicates."""
    try:
        result = supabase.table("answer").select("question_id").eq("survey_submission_id", submission_id).execute()
        if result.data:
            return [answer["question_id"] for answer in result.data]
        else:
            return []
    except Exception as e:
        print(f"Error getting existing answers: {e}")
        return []

def get_existing_answers_for_survey_response(survey_response_id):
    """Get existing answers for a survey response to avoid duplicates (legacy wrapper)."""
    return get_existing_answers_for_survey_submission(survey_response_id)

# Keep the old function name for backward compatibility
def get_existing_answers_for_call(call_id):
    """Get existing answers for a call to avoid duplicates (legacy wrapper)."""
    return get_existing_answers_for_survey_submission(call_id)

def cleanup_duplicate_survey_submissions():
    """Utility function to clean up duplicate survey submissions for the same room."""
    try:
        # Get all survey submissions grouped by room_name
        result = supabase.table("survey_submissions").select("*").order("room_name").order("created_at").execute()
        
        if not result.data:
            print("No survey submissions found")
            return
        
        room_submissions = {}
        for submission in result.data:
            room_name = submission['room_name']
            if room_name not in room_submissions:
                room_submissions[room_name] = []
            room_submissions[room_name].append(submission)
        
        # Find and remove duplicates (keep the first one)
        for room_name, submissions in room_submissions.items():
            if len(submissions) > 1:
                print(f"Found {len(submissions)} duplicate submissions for room: {room_name}")
                # Keep the first submission, delete the rest
                submissions_to_delete = submissions[1:]
                for submission in submissions_to_delete:
                    print(f"Deleting duplicate survey submission ID: {submission['id']}")
                    # First delete associated answers
                    supabase.table("answer").delete().eq("survey_submission_id", submission['id']).execute()
                    # Then delete the survey submission
                    supabase.table("survey_submissions").delete().eq("id", submission['id']).execute()
                    
    except Exception as e:
        print(f"Error cleaning up duplicates: {e}")

def cleanup_duplicate_survey_responses():
    """Utility function to clean up duplicate survey responses for the same room (legacy wrapper)."""
    return cleanup_duplicate_survey_submissions()

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
        closing="Thank you for completing this survey. We value your input.",
        campaign_type="phone_survey"
    )

    # Add all questions from survey_questions.json
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)
    for q_num in sorted(questions, key=lambda x: int(x)):
        q_text = questions[q_num]
        qid = add_question(campaign_id, q_text, int(q_num))