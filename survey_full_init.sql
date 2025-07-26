PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
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
INSERT INTO campaign VALUES(1,'InnoVet-AMR 2024','Survey on climate change, AMR, and animal health.',NULL,NULL,'You are the automated survey agent for the InnoVet-AMR initiative.','Thank you for taking part in our InnoVet-AMR survey.','Hello, welcome to our survey.','Thank you for completing this survey. We value your input.');
CREATE TABLE question (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_order INTEGER NOT NULL
);
INSERT INTO question VALUES(1,1,'What are your top three trends that are driving change in this space?',1);
INSERT INTO question VALUES(2,1,'What are some of the biggest challenges and issues you are experiencing?',2);
INSERT INTO question VALUES(3,1,'What new opportunities do you see to leverage innovation?',3);
CREATE TABLE call (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number VARCHAR(32) NOT NULL,
    campaign_id INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    call_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    s3_recording_url TEXT,
    UNIQUE(phone_number, campaign_id, call_timestamp)
);
INSERT INTO call VALUES(1,'+15145859691',1,'2025-07-26 17:20:47',NULL);
INSERT INTO call VALUES(2,'+15145859691',1,'2025-07-26 17:27:15',NULL);
INSERT INTO call VALUES(3,'+15145859691',1,'2025-07-26 17:39:40','s3://s3-photo-ai-saas/future_survey/20250726_133939_15145859691_call-_+15145859691_NCx7Lbnwwh5o.mp4');
CREATE TABLE answer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id INTEGER NOT NULL REFERENCES call(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES question(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(call_id, question_id)
);
INSERT INTO answer VALUES(1,1,1,'Wildfire, ice melting in Antarctica, destruction of community forest in Amazonia.','2025-07-26 17:21:59');
INSERT INTO answer VALUES(2,1,2,'Quality of care in Montreal, heat dose wave in summer in Montreal, quality of water in Montreal.','2025-07-26 17:21:59');
INSERT INTO answer VALUES(3,1,3,'Use AI to better understand changes and tackle problems, modify government policy to take into account those changes.','2025-07-26 17:21:59');
INSERT INTO answer VALUES(4,2,1,'Canadian wildfire, Arctic ice meltdown, Amazonian forest destruction','2025-07-26 17:28:32');
INSERT INTO answer VALUES(5,2,2,'Quality of air in Montreal in summer, heatwave in summer, quality of water in Montreal.','2025-07-26 17:28:32');
INSERT INTO answer VALUES(6,2,3,'Use AI to better understand change, use AI to help tackle those changes, modify government policy to better take into account those issues.','2025-07-26 17:28:32');
INSERT INTO answer VALUES(7,3,1,'Meltdown of ice in Antarctic, wildfire in Canada, and changes in the Amazon forest.','2025-07-26 17:41:39');
INSERT INTO answer VALUES(8,3,2,'Quality offer in Montreal and on summer, and quality of water the whole year.','2025-07-26 17:41:39');
INSERT INTO answer VALUES(9,3,3,'Use AI to better understand and solve those phenomena, and adjust the government policy to take into account those changes.','2025-07-26 17:41:39');
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('campaign',1);
INSERT INTO sqlite_sequence VALUES('question',3);
INSERT INTO sqlite_sequence VALUES('call',3);
INSERT INTO sqlite_sequence VALUES('answer',9);
COMMIT;
