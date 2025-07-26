import sqlite3
from pathlib import Path
import json

DB_PATH = "survey.db"
SCHEMA_PATH = "survey_schema.sql"
QUESTIONS_PATH = "survey_questions.json"

def init_db(db_path=DB_PATH, schema_path=SCHEMA_PATH):
    if not Path(db_path).exists():
        with sqlite3.connect(db_path) as conn:
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
            print(f"Database initialized at {db_path}")
    else:
        print(f"Database already exists at {db_path}")

def create_campaign(name, description=None, start_date=None, end_date=None,
                    intro_prompt=None, purpose_explanation=None, greeting=None, closing=None, db_path=DB_PATH):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO campaign (name, description, start_date, end_date, intro_prompt, purpose_explanation, greeting, closing)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, start_date, end_date, intro_prompt, purpose_explanation, greeting, closing))
        conn.commit()
        return cur.lastrowid

def add_question(campaign_id, question_text, question_order, db_path=DB_PATH):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO question (campaign_id, question_text, question_order)
            VALUES (?, ?, ?)
        ''', (campaign_id, question_text, question_order))
        conn.commit()
        return cur.lastrowid

def record_call(phone_number, campaign_id, call_timestamp=None, s3_recording_url=None, db_path=DB_PATH):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO call (phone_number, campaign_id, call_timestamp, s3_recording_url)
            VALUES (?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?)
        ''', (phone_number, campaign_id, call_timestamp, s3_recording_url))
        conn.commit()
        return cur.lastrowid

def record_answer(call_id, question_id, answer_text, answered_at=None, db_path=DB_PATH):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO answer (call_id, question_id, answer_text, answered_at)
            VALUES (?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
        ''', (call_id, question_id, answer_text, answered_at))
        conn.commit()
        return cur.lastrowid

# Example usage
if __name__ == "__main__":
    init_db()
    # Create a campaign
    campaign_id = create_campaign(
        name="InnoVet-AMR 2024",
        description="Survey on climate change, AMR, and animal health.",
        intro_prompt="You are the automated survey agent for the InnoVet-AMR initiative...",
        purpose_explanation="Thank you for taking part in our InnoVet-AMR survey...",
        greeting="Hello, welcome to our survey.",
        closing="Thank you for completing this survey. We value your input."
    )
    print(f"Created campaign with id: {campaign_id}")

    # Add all questions from survey_questions.json
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)
    for q_num in sorted(questions, key=lambda x: int(x)):
        q_text = questions[q_num]
        qid = add_question(campaign_id, q_text, int(q_num))
        print(f"Added question {q_num} with id: {qid}")

    # Record a call with the provided S3 URL
    s3_recording_url = "s3://s3-photo-ai-saas/future_survey/20250726_110446_15145859691_call-_+15145859691_cNDqHJJ3rZqi.mp4"
    call_id = record_call("+1234567890", campaign_id, s3_recording_url=s3_recording_url)
    print(f"Recorded call with id: {call_id}")

    # Record an answer (for the first question as an example)
    first_qid = 1
    answer_id = record_answer(call_id, first_qid, "My main concern is antibiotic misuse.")
    print(f"Recorded answer with id: {answer_id}") 