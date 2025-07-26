-- Survey System SQL Schema
-- Supports campaigns, questions, answers, call records, and campaign-specific prompts

-- 1. Campaign table: stores campaign metadata and all prompt phrases
CREATE TABLE campaign (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    intro_prompt TEXT,           -- e.g., "You are the automated survey agent for ..."
    purpose_explanation TEXT,    -- e.g., "Thank you for taking part in our ..."
    greeting TEXT,               -- e.g., "Hello, welcome to our survey."
    closing TEXT                 -- e.g., "Thank you for completing this survey..."
);

-- 2. Question table: stores questions for each campaign
CREATE TABLE question (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_order INTEGER NOT NULL
);

-- 3. Call table: represents a unique call session (one survey attempt by a participant)
CREATE TABLE call (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number VARCHAR(32) NOT NULL,
    campaign_id INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    call_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    s3_recording_url TEXT,
    UNIQUE(phone_number, campaign_id, call_timestamp)
);

-- 4. Answer table: stores answers to questions, linked to both the call and the question
CREATE TABLE answer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id INTEGER NOT NULL REFERENCES call(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES question(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(call_id, question_id)
); 