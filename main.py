
import logging
import os
import json
import boto3
from botocore.exceptions import ClientError

from datetime import datetime, timezone
from typing import Annotated

from dotenv import load_dotenv
from livekit import agents
from livekit import api, rtc
from livekit.agents import (Agent, AgentSession,
                            JobProcess, RoomInputOptions,
                            RunContext, function_tool)
from livekit.plugins import deepgram, noise_cancellation, openai, silero
from livekit.agents import get_job_context
from pydantic import Field
from twilio.rest import Client
import re

from user_data import UserData
from recording import start_s3_recording

load_dotenv()

logger = logging.getLogger("futures_survey_assistant")
logger.setLevel(logging.INFO)
    
RunContext_T = RunContext[UserData]

def load_survey_questions(path="survey_questions.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

SURVEY_QUESTIONS = load_survey_questions()

def build_dynamic_prompt() -> str:
    """Build the survey prompt dynamically based on the questions configuration"""
    current_time = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')
    
    # Build the questions section dynamically
    questions_section = ""
    for q_num, question in SURVEY_QUESTIONS.items():
        questions_section += f"\n{int(q_num) + 1}) Question {q_num}:\n   \"{question}\"\n"
    
    prompt = f"""
You are the automated survey agent for the InnoVet-AMR initiative on climate change, antimicrobial resistance (AMR), and animal health.
Current date and time: {current_time}

LANGUAGE POLICY
Detect the participant's first reply.
Do not switch languages once the conversation has started, even if the participant does.
Never use special characters such as %, $, #, or *.

SURVEY FLOW (ask only one question at a time)

1) Briefly explain purpose:
   "Thank you for taking part in our InnoVet-AMR survey. We are collecting insights on trends and the changing landscape of climate change, AMR, and animal health."
{questions_section}

{len(SURVEY_QUESTIONS) + 3}) Completion check:
   After the recap, call check_survey_complete to ensure all three questions were answered.

{len(SURVEY_QUESTIONS) + 4}) Closing:
   If complete, say:
   "Thank you for completing this survey. We value your input and look forward to you participating in our other research."
   Then immediately end the call using the end_call function.

GENERAL GUIDELINES
Ask only one question at a time.
Respond in clear, complete sentences.
If the participant provides unexpected information, politely steer them back to the current question.
Do not provide medical or technical advice; clarify that your role is limited to conducting this survey.
If the participant asks for information outside your scope, respond succinctly that you can only administer the survey.
"""
    return prompt

class MainAgent(Agent):
    def __init__(self) -> None:
        # Use the dynamic prompt builder
        MAIN_PROMPT = build_dynamic_prompt()
            
        logger.info("MainAgent initialized with dynamic prompt: %s", MAIN_PROMPT)
       
        super().__init__(
            instructions=MAIN_PROMPT,
            tools=[set_questionnaire_answer, check_survey_complete],
            tts=openai.TTS(voice="nova"),
        )
        
    async def on_enter(self) -> None:
        await self.session.say(
            "Hello, welcome to our survey.",
            allow_interruptions=False,
        )

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def save_userdata_to_s3(userdata: UserData) -> bool:
    """Save userdata as JSON to S3 bucket with phone number, future_survey, and date in filename"""
    try:
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        s3_bucket = "s3-photo-ai-saas"
        
        if not all([aws_access_key, aws_secret_key]):
            logger.error("Missing AWS credentials for S3 upload")
            return False
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        phone_suffix = userdata.customer_phone.replace('+', '').replace('-', '') if userdata.customer_phone else 'unknown'
        filename = f"future_survey/{phone_suffix}_future_survey_{timestamp}.json"
        
        # Optimized JSON structure
        userdata_dict = {
            "customer": {
                "first_name": userdata.customer_first_name,
                "last_name": userdata.customer_last_name,
                "phone": userdata.customer_phone,
            },
            "answers": [
                {
                    "question_number": q_num,
                    "question": SURVEY_QUESTIONS.get(q_num, "Unknown question"),
                    "answer": answer
                } for q_num, answer in userdata.questionnaire_answers.items()
            ],
            "recording_id": userdata.recording_id,
            "timestamp": timestamp
        }
        
        json_data = json.dumps(userdata_dict, indent=2, ensure_ascii=False)
        
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=filename,
            Body=json_data,
            ContentType='application/json'
        )
        
        logger.info(f"Userdata saved to S3: s3://{s3_bucket}/{filename}")
        return True
        
    except ClientError as e:
        logger.error(f"S3 upload error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error saving userdata to S3: {e}")
        return False
    
@function_tool    
async def set_questionnaire_answer(
    question_number: Annotated[str, Field(description="The question number (e.g., '1', '2', '3')")],
    answer: Annotated[str, Field(description="The answer")], 
    ctx: RunContext_T
) -> str:
    """
    Set questionnaire answers in the user data with question number as key.
    """
    userdata = ctx.userdata
    userdata.questionnaire_answers[question_number] = answer
    logger.info(f"Question {question_number} answer set: {answer}")
    logger.info(f"All questionnaire answers: {userdata.questionnaire_answers}")
    
    # No S3 save here; only at the end
    if len(userdata.questionnaire_answers) == len(SURVEY_QUESTIONS):
        return f"Answer for question {question_number} has been saved successfully. Survey complete - ready for finalization: {answer}"
    else:
        return f"Answer for question {question_number} has been saved successfully: {answer}"

@function_tool
async def check_survey_complete(ctx: RunContext_T) -> str:
    """
    Check if the survey is complete and save to S3 if all questions are answered.
    """
    userdata = ctx.userdata
    total_questions = len(SURVEY_QUESTIONS)
    answered_questions = len(userdata.questionnaire_answers)
    
    logger.info(f"Survey completion check: {answered_questions}/{total_questions} questions answered")
    
    if answered_questions == total_questions:
        # Save complete survey to S3
        s3_success = await save_userdata_to_s3(userdata)
        if s3_success:
            logger.info("Survey completed - all data saved to S3")
            return f"Survey is complete! All {total_questions} questions have been answered and data has been saved to S3."
        else:
            logger.warning("Survey completed but S3 save failed")
            return f"Survey is complete! All {total_questions} questions have been answered but S3 backup failed."
    else:
        missing_questions = [q for q in SURVEY_QUESTIONS.keys() if q not in userdata.questionnaire_answers]
        return f"Survey is not complete. {answered_questions}/{total_questions} questions answered. Missing questions: {missing_questions}"
    
def extract_phone_from_room_name(room_name: str) -> str:
    """
    Extract phone number from room name like 'call-_+15145859691_yZ35TYo5aNjy'
    Returns the phone number or None if not found
    """
    pattern = r'call-_(\+\d+)_'
    match = re.search(pattern, room_name)
    
    if match:
        return match.group(1)
    
    return None
    
async def entrypoint(ctx: agents.JobContext):
    
   # Get room info and extract phone number
    room = ctx.room
    room_name = room.name
    
    phone_number = extract_phone_from_room_name(room_name)
    
    userdata = UserData()
    userdata.customer_phone = phone_number if phone_number else None
  
    logger.info(f"Room name: {room_name}")
    logger.info(f"Phone number: {phone_number}")

    
    userdata.agents.update({
        "main_agent": MainAgent(),
    })
    
    recording_success = await start_s3_recording(room_name, userdata)
    if recording_success:
        logger.info("S3 Recording started successfully")
    else:
        logger.warning("S3 Recording failed, continuing without recording")    
    await ctx.connect()
    
    
    # Use optimized session class
    session = AgentSession(
        userdata=userdata,
        stt=deepgram.STT(model="nova-3", language="en-US"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="nova"),
        vad=silero.VAD.load(),
        max_tool_steps=5,
    )
    
    # Store session reference in userdata for access in function tools
    userdata.session = session
    
    await session.start(
        agent=userdata.agents["main_agent"],
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

if __name__ == "__main__": 
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name="alex-telephony-agent"))
