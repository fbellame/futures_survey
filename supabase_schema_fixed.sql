-- Survey System SQL Schema for Supabase (PostgreSQL) - Fixed Version
-- Supports campaigns, questions, answers, call records, and campaign-specific prompts

-- 1. Campaign table: stores campaign metadata and all prompt phrases
CREATE TABLE campaign (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    intro_prompt TEXT,           -- e.g., "You are the automated survey agent for ..."
    purpose_explanation TEXT,    -- e.g., "Thank you for taking part in our ..."
    greeting TEXT,               -- e.g., "Hello, welcome to our survey."
    closing TEXT,                -- e.g., "Thank you for completing this survey..."
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Question table: stores questions for each campaign
CREATE TABLE question (
    id BIGSERIAL PRIMARY KEY,
    campaign_id BIGINT NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Call table: represents a unique call session (one survey attempt by a participant)
-- Removed the problematic unique constraint that was causing issues
CREATE TABLE call (
    id BIGSERIAL PRIMARY KEY,
    phone_number VARCHAR(32) NOT NULL,
    campaign_id BIGINT NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    call_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    s3_recording_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Answer table: stores answers to questions, linked to both the call and the question
CREATE TABLE answer (
    id BIGSERIAL PRIMARY KEY,
    call_id BIGINT NOT NULL REFERENCES call(id) ON DELETE CASCADE,
    question_id BIGINT NOT NULL REFERENCES question(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    answered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(call_id, question_id)
);

-- Create indexes for better performance
CREATE INDEX idx_campaign_id ON question(campaign_id);
CREATE INDEX idx_call_campaign_id ON call(campaign_id);
CREATE INDEX idx_call_timestamp ON call(call_timestamp);
CREATE INDEX idx_answer_call_id ON answer(call_id);
CREATE INDEX idx_answer_question_id ON answer(question_id);

-- Enable Row Level Security (RLS) - you can disable this if you want public access
ALTER TABLE campaign ENABLE ROW LEVEL SECURITY;
ALTER TABLE question ENABLE ROW LEVEL SECURITY;
ALTER TABLE call ENABLE ROW LEVEL SECURITY;
ALTER TABLE answer ENABLE ROW LEVEL SECURITY;

-- Create policies for anonymous access (adjust as needed for your security requirements)
CREATE POLICY "Allow anonymous read access to campaign" ON campaign FOR SELECT USING (true);
CREATE POLICY "Allow anonymous read access to question" ON question FOR SELECT USING (true);
CREATE POLICY "Allow anonymous read access to call" ON call FOR SELECT USING (true);
CREATE POLICY "Allow anonymous read access to answer" ON answer FOR SELECT USING (true);

CREATE POLICY "Allow anonymous insert access to campaign" ON campaign FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anonymous insert access to question" ON question FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anonymous insert access to call" ON call FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anonymous insert access to answer" ON answer FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow anonymous update access to call" ON call FOR UPDATE USING (true);
CREATE POLICY "Allow anonymous update access to answer" ON answer FOR UPDATE USING (true); 