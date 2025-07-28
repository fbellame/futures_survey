
import logging

from datetime import datetime, timezone
from typing import Annotated

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (Agent, AgentSession,
                            JobProcess, RoomInputOptions,
                            RunContext, function_tool)
from livekit.plugins import deepgram, noise_cancellation, openai, silero
from pydantic import Field
import re

from user_data import UserData
from recording import start_s3_recording

# --- New imports for DB integration ---
from db_manager import (
    record_call, record_answer, 
    get_campaign_from_db, get_questions_for_campaign, update_call_s3_url,
    get_campaign_by_room_name, get_campaign_by_id
)

load_dotenv()

logger = logging.getLogger("futures_survey_assistant")
logger.setLevel(logging.INFO)

# Suppress hpack debug logs
logging.getLogger("hpack.hpack").setLevel(logging.WARNING)
    
RunContext_T = RunContext[UserData]

# These functions are now imported from db_manager.py

def build_dynamic_prompt_from_db(campaign):
    """Build dynamic prompt from a specific campaign."""
    questions = get_questions_for_campaign(campaign["id"])
    current_time = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')
    questions_section = ""
    for qid, qtext, qorder in questions:
        questions_section += f"\n{qorder}) Question {qorder}:\n   \"{qtext}\"\n"
    prompt = f"""
{campaign['intro_prompt']}
Current date and time: {current_time}

LANGUAGE POLICY
Detect the participant's first reply.
Do not switch languages once the conversation has started, even if the participant does.
Never use special characters such as %, $, #, or *.

SURVEY FLOW (ask only one question at a time)

1) Briefly explain purpose:
   \"{campaign['purpose_explanation']}\"
{questions_section}
{len(questions) + 3}) Completion check:
   After the recap, call check_survey_complete to ensure all questions were answered.

{len(questions) + 4}) Closing:
   If complete, say:
   \"{campaign['closing']}\"
   Then immediately end the call using the end_call function.

GENERAL GUIDELINES
Ask only one question at a time.
Respond in clear, complete sentences.
If the participant provides unexpected information, politely steer them back to the current question.
Do not provide medical or technical advice; clarify that your role is limited to conducting this survey.
If the participant asks for information outside your scope, respond succinctly that you can only administer the survey.
"""
    return prompt, campaign, questions

class MainAgent(Agent):
    def __init__(self, campaign, questions) -> None:
        MAIN_PROMPT, self.campaign, self.questions = build_dynamic_prompt_from_db(campaign)
        logger.info(f"MainAgent initialized for campaign '{campaign['name']}' with dynamic prompt: %s", MAIN_PROMPT)
        super().__init__(
            instructions=MAIN_PROMPT,
            tools=[set_questionnaire_answer, check_survey_complete],
            tts=openai.TTS(voice="nova"),
        )
    async def on_enter(self) -> None:
        await self.session.say(
            self.campaign["greeting"] or "Hello, welcome to our survey.",
            allow_interruptions=False,
        )

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

# --- Remove S3 JSON save, use DB instead ---
async def save_userdata_to_db(userdata: UserData, campaign_id: int, call_id: int):
    # Save S3 recording URL if present
    if getattr(userdata, 's3_recording_url', None):
        update_call_s3_url(call_id, userdata.s3_recording_url)
        logger.info(f"Updated call {call_id} with S3 recording URL: {userdata.s3_recording_url}")
    elif getattr(userdata, 'recording_id', None):
        # Optionally, if you have a way to build the S3 URL from recording_id, do it here
        pass
    
    # Get existing answers to avoid duplicates
    from db_manager import get_existing_answers_for_call
    existing_question_ids = get_existing_answers_for_call(call_id)
    
    # Save all answers to DB
    for q_num, answer in userdata.questionnaire_answers.items():
        # Get question ID from Supabase
        questions = get_questions_for_campaign(campaign_id)
        question_id = None
        for q_id, q_text, q_order in questions:
            if q_order == int(q_num):
                question_id = q_id
                break
        
        if question_id:
            # Only record if this question hasn't been answered yet
            if question_id not in existing_question_ids:
                record_answer(call_id, question_id, answer)
                logger.info(f"Saved answer for question {q_num} to DB.")
            else:
                logger.info(f"Answer for question {q_num} already exists, skipping.")
        else:
            logger.warning(f"Question id not found for campaign {campaign_id}, order {q_num}")
    return True
    
@function_tool    
async def set_questionnaire_answer(
    question_number: Annotated[str, Field(description="The question number (e.g., '1', '2', '3')")],
    answer: Annotated[str, Field(description="The answer")], 
    ctx: RunContext_T
) -> str:
    userdata = ctx.userdata
    userdata.questionnaire_answers[question_number] = answer
    logger.info(f"Question {question_number} answer set: {answer}")
    logger.info(f"All questionnaire answers: {userdata.questionnaire_answers}")
    if len(userdata.questionnaire_answers) == len(userdata.questions):
        return f"Answer for question {question_number} has been saved successfully. Survey complete - ready for finalization: {answer}"
    else:
        return f"Answer for question {question_number} has been saved successfully: {answer}"

@function_tool
async def check_survey_complete(ctx: RunContext_T) -> str:
    userdata = ctx.userdata
    total_questions = len(userdata.questions)
    answered_questions = len(userdata.questionnaire_answers)
    logger.info(f"Survey completion check: {answered_questions}/{total_questions} questions answered")
    if answered_questions == total_questions:
        # Save complete survey to DB
        await save_userdata_to_db(userdata, userdata.campaign["id"], userdata.call_id)
        logger.info("Survey completed - all data saved to DB")
        return f"Survey is complete! All {total_questions} questions have been answered and data has been saved to the database."
    else:
        missing_questions = [str(q[2]) for q in userdata.questions if str(q[2]) not in userdata.questionnaire_answers]
        return f"Survey is not complete. {answered_questions}/{total_questions} questions answered. Missing questions: {missing_questions}"

def extract_phone_from_room_name(room_name: str) -> str:
    pattern = r'call-_(\+\d+)_'
    match = re.search(pattern, room_name)
    if match:
        return match.group(1)
    return None
    
async def entrypoint(ctx: agents.JobContext):
    room = ctx.room
    room_name = room.name
    phone_number = extract_phone_from_room_name(room_name)
    userdata = UserData()
    userdata.customer_phone = phone_number if phone_number else None
    logger.info(f"Room name: {room_name}")
    logger.info(f"Phone number: {phone_number}")
    
    # Select campaign based on room name
    campaign = get_campaign_by_room_name(room_name)
    logger.info(f"Selected campaign: {campaign['name']} (ID: {campaign['id']})")
    
    # Get questions for the selected campaign
    questions = get_questions_for_campaign(campaign["id"])
    logger.info(f"Loaded {len(questions)} questions for campaign {campaign['id']}")
    
    userdata.agents.update({
        "main_agent": MainAgent(campaign, questions),
    })
    userdata.questions = userdata.agents["main_agent"].questions
    userdata.campaign = campaign  # Store campaign dict in userdata
    
    # Start S3 voice recording before recording the call in the DB
    recording_success = await start_s3_recording(room_name, userdata)
    if recording_success:
        logger.info("S3 Recording started successfully")
    else:
        logger.warning("S3 Recording failed, continuing without recording")
        userdata.s3_recording_url = None  # Explicitly set to None if failed
    
    # Record the call in the DB with room name
    call_id = record_call(phone_number or "unknown", campaign["id"], room_name, s3_recording_url=userdata.s3_recording_url)
    userdata.call_id = call_id
    logger.info(f"Call recorded in DB with id: {call_id}")
    
    await ctx.connect()
    session = AgentSession(
        userdata=userdata,
        stt=deepgram.STT(model="nova-3", language="en-US"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="nova"),
        vad=silero.VAD.load(),
        max_tool_steps=5,
    )
    userdata.session = session
    await session.start(
        agent=userdata.agents["main_agent"],
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

if __name__ == "__main__": 
    #agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name="alex-telephony-agent"))
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
