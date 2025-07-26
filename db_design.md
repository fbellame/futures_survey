# Database Design for Survey Campaigns, Questions, Answers, and Call Recordings

## Overview
This schema is designed to support:
- Multiple survey campaigns
- Questions associated with each campaign
- Answers from participants (identified by phone number and call)
- Storage of S3 links to call recordings

## Entity-Relationship Diagram (ERD)

```
Campaign ──< Question ──< Answer >── Call
                        ^           ^
                        |           |
                    (by question) (by call)
```

## Table Definitions

### 1. campaign
Stores metadata about each survey campaign.

```sql
CREATE TABLE campaign (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE
);
```

### 2. question
Stores questions for each campaign.

```sql
CREATE TABLE question (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_order INTEGER NOT NULL
);
```

### 3. call
Represents a unique call session (one survey attempt by a participant).

```sql
CREATE TABLE call (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(32) NOT NULL,
    campaign_id INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    call_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    s3_recording_url TEXT,
    UNIQUE(phone_number, campaign_id, call_timestamp)
);
```

### 4. answer
Stores answers to questions, linked to both the call and the question.

```sql
CREATE TABLE answer (
    id SERIAL PRIMARY KEY,
    call_id INTEGER NOT NULL REFERENCES call(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES question(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    answered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(call_id, question_id)
);
```

## Rationale
- **campaign**: Allows for multiple, time-bounded survey campaigns.
- **question**: Each question is linked to a campaign and has an explicit order.
- **call**: Each call is a unique survey attempt by a participant (phone number), stores the S3 link to the recording, and is linked to a campaign.
- **answer**: Each answer is linked to both a call and a question, ensuring answers are tracked per participant per call.

## Example Query: Retrieve All Answers for a Campaign
```sql
SELECT c.phone_number, q.question_text, a.answer_text, c.s3_recording_url
FROM answer a
JOIN call c ON a.call_id = c.id
JOIN question q ON a.question_id = q.id
WHERE c.campaign_id = 1
ORDER BY c.phone_number, q.question_order;
```

---

This schema is normalized, supports multiple campaigns, and is extensible for future requirements (e.g., user authentication, survey branching, etc.). 