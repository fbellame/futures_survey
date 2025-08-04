SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

COMMENT ON SCHEMA "public" IS 'standard public schema';

CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";
CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";
CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";

SET default_tablespace = '';
SET default_table_access_method = "heap";

CREATE TABLE IF NOT EXISTS "public"."answer" (
    "id" bigint NOT NULL,
    "survey_response_id" bigint NOT NULL,
    "question_id" bigint NOT NULL,
    "answer_text" "text" NOT NULL,
    "answered_at" timestamp with time zone DEFAULT "now"(),
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);

ALTER TABLE "public"."answer" OWNER TO "postgres";

CREATE SEQUENCE IF NOT EXISTS "public"."answer_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE "public"."answer_id_seq" OWNER TO "postgres";
ALTER SEQUENCE "public"."answer_id_seq" OWNED BY "public"."answer"."id";

CREATE TABLE IF NOT EXISTS "public"."campaign" (
    "id" bigint NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "start_date" "date",
    "end_date" "date",
    "intro_prompt" "text",
    "purpose_explanation" "text",
    "greeting" "text",
    "closing" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "campaign_type" "text" DEFAULT 'web_survey'::"text" NOT NULL,
    "campaign_uri" "text",
    CONSTRAINT "campaign_campaign_type_check" CHECK (("campaign_type" = ANY (ARRAY['web_survey'::"text", 'phone_survey'::"text"])))
);

ALTER TABLE "public"."campaign" OWNER TO "postgres";

CREATE SEQUENCE IF NOT EXISTS "public"."campaign_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE "public"."campaign_id_seq" OWNER TO "postgres";
ALTER SEQUENCE "public"."campaign_id_seq" OWNED BY "public"."campaign"."id";

CREATE TABLE IF NOT EXISTS "public"."campaign_room_mapping" (
    "id" bigint NOT NULL,
    "campaign_id" bigint NOT NULL,
    "room_pattern" "text" NOT NULL,
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);

ALTER TABLE "public"."campaign_room_mapping" OWNER TO "postgres";

CREATE SEQUENCE IF NOT EXISTS "public"."campaign_room_mapping_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE "public"."campaign_room_mapping_id_seq" OWNER TO "postgres";
ALTER SEQUENCE "public"."campaign_room_mapping_id_seq" OWNED BY "public"."campaign_room_mapping"."id";

CREATE TABLE IF NOT EXISTS "public"."question" (
    "id" bigint NOT NULL,
    "campaign_id" bigint NOT NULL,
    "question_text" "text" NOT NULL,
    "question_order" integer NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);

ALTER TABLE "public"."question" OWNER TO "postgres";

CREATE SEQUENCE IF NOT EXISTS "public"."question_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE "public"."question_id_seq" OWNER TO "postgres";
ALTER SEQUENCE "public"."question_id_seq" OWNED BY "public"."question"."id";

CREATE TABLE IF NOT EXISTS "public"."survey_response" (
    "id" bigint NOT NULL,
    "phone_number" character varying(32) NOT NULL,
    "campaign_id" bigint NOT NULL,
    "room_name" "text" NOT NULL,
    "call_timestamp" timestamp with time zone DEFAULT "now"(),
    "s3_recording_url" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."survey_response" OWNER TO "postgres";

CREATE SEQUENCE IF NOT EXISTS "public"."survey_response_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."survey_response_id_seq" OWNER TO "postgres";
ALTER SEQUENCE "public"."survey_response_id_seq" OWNED BY "public"."survey_response"."id";

ALTER TABLE ONLY "public"."answer" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."answer_id_seq"'::"regclass");
ALTER TABLE ONLY "public"."campaign" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."campaign_id_seq"'::"regclass");
ALTER TABLE ONLY "public"."campaign_room_mapping" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."campaign_room_mapping_id_seq"'::"regclass");
ALTER TABLE ONLY "public"."question" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."question_id_seq"'::"regclass");
ALTER TABLE ONLY "public"."survey_response" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."survey_response_id_seq"'::"regclass");

ALTER TABLE ONLY "public"."answer"
    ADD CONSTRAINT "answer_call_id_question_id_key" UNIQUE ("survey_response_id", "question_id");

ALTER TABLE ONLY "public"."answer"
    ADD CONSTRAINT "answer_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "public"."campaign"
    ADD CONSTRAINT "campaign_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "public"."campaign_room_mapping"
    ADD CONSTRAINT "campaign_room_mapping_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "public"."campaign_room_mapping"
    ADD CONSTRAINT "campaign_room_mapping_room_pattern_key" UNIQUE ("room_pattern");

ALTER TABLE ONLY "public"."campaign"
    ADD CONSTRAINT "campaign_uri_unique" UNIQUE ("campaign_uri");

ALTER TABLE ONLY "public"."question"
    ADD CONSTRAINT "question_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "public"."survey_response"
    ADD CONSTRAINT "survey_response_pkey" PRIMARY KEY ("id");

CREATE INDEX "idx_answer_call_id" ON "public"."answer" USING "btree" ("survey_response_id");
CREATE INDEX "idx_answer_question_id" ON "public"."answer" USING "btree" ("question_id");
CREATE INDEX "idx_call_campaign_id" ON "public"."survey_response" USING "btree" ("campaign_id");
CREATE INDEX "idx_call_room_name" ON "public"."survey_response" USING "btree" ("room_name");
CREATE INDEX "idx_call_timestamp" ON "public"."survey_response" USING "btree" ("call_timestamp");
CREATE INDEX "idx_campaign_id" ON "public"."question" USING "btree" ("campaign_id");
CREATE INDEX "idx_campaign_room_mapping_campaign_id" ON "public"."campaign_room_mapping" USING "btree" ("campaign_id");
CREATE INDEX "idx_campaign_room_mapping_pattern" ON "public"."campaign_room_mapping" USING "btree" ("room_pattern");
CREATE INDEX "idx_campaign_uri" ON "public"."campaign" USING "btree" ("campaign_uri");

ALTER TABLE ONLY "public"."answer"
    ADD CONSTRAINT "answer_call_id_fkey" FOREIGN KEY ("survey_response_id") REFERENCES "public"."survey_response"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."answer"
    ADD CONSTRAINT "answer_question_id_fkey" FOREIGN KEY ("question_id") REFERENCES "public"."question"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."survey_response"
    ADD CONSTRAINT "call_campaign_id_fkey" FOREIGN KEY ("campaign_id") REFERENCES "public"."campaign"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."campaign_room_mapping"
    ADD CONSTRAINT "campaign_room_mapping_campaign_id_fkey" FOREIGN KEY ("campaign_id") REFERENCES "public"."campaign"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "public"."question"
    ADD CONSTRAINT "question_campaign_id_fkey" FOREIGN KEY ("campaign_id") REFERENCES "public"."campaign"("id") ON DELETE CASCADE;

CREATE POLICY "Allow anonymous delete access to answer" ON "public"."answer" FOR DELETE USING (true);
CREATE POLICY "Allow anonymous delete access to campaign" ON "public"."campaign" FOR DELETE USING (true);
CREATE POLICY "Allow anonymous delete access to campaign_room_mapping" ON "public"."campaign_room_mapping" FOR DELETE USING (true);
CREATE POLICY "Allow anonymous delete access to question" ON "public"."question" FOR DELETE USING (true);
CREATE POLICY "Allow anonymous delete access to survey_response" ON "public"."survey_response" FOR DELETE USING (true);
CREATE POLICY "Allow anonymous insert access to answer" ON "public"."answer" FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anonymous insert access to campaign" ON "public"."campaign" FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anonymous insert access to campaign_room_mapping" ON "public"."campaign_room_mapping" FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anonymous insert access to question" ON "public"."question" FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anonymous insert access to survey_response" ON "public"."survey_response" FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anonymous read access to answer" ON "public"."answer" FOR SELECT USING (true);
CREATE POLICY "Allow anonymous read access to campaign" ON "public"."campaign" FOR SELECT USING (true);
CREATE POLICY "Allow anonymous read access to campaign_room_mapping" ON "public"."campaign_room_mapping" FOR SELECT USING (true);
CREATE POLICY "Allow anonymous read access to question" ON "public"."question" FOR SELECT USING (true);
CREATE POLICY "Allow anonymous read access to survey_response" ON "public"."survey_response" FOR SELECT USING (true);
CREATE POLICY "Allow anonymous update access to answer" ON "public"."answer" FOR UPDATE USING (true);
CREATE POLICY "Allow anonymous update access to campaign" ON "public"."campaign" FOR UPDATE USING (true);
CREATE POLICY "Allow anonymous update access to campaign_room_mapping" ON "public"."campaign_room_mapping" FOR UPDATE USING (true);
CREATE POLICY "Allow anonymous update access to survey_response" ON "public"."survey_response" FOR UPDATE USING (true);

ALTER TABLE "public"."answer" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."campaign" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."campaign_room_mapping" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."question" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."survey_response" ENABLE ROW LEVEL SECURITY;
ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";

GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";

GRANT ALL ON TABLE "public"."answer" TO "anon";
GRANT ALL ON TABLE "public"."answer" TO "authenticated";
GRANT ALL ON TABLE "public"."answer" TO "service_role";

GRANT ALL ON SEQUENCE "public"."answer_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."answer_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."answer_id_seq" TO "service_role";

GRANT ALL ON TABLE "public"."campaign" TO "anon";
GRANT ALL ON TABLE "public"."campaign" TO "authenticated";
GRANT ALL ON TABLE "public"."campaign" TO "service_role";

GRANT ALL ON SEQUENCE "public"."campaign_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."campaign_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."campaign_id_seq" TO "service_role";

GRANT ALL ON TABLE "public"."campaign_room_mapping" TO "anon";
GRANT ALL ON TABLE "public"."campaign_room_mapping" TO "authenticated";
GRANT ALL ON TABLE "public"."campaign_room_mapping" TO "service_role";

GRANT ALL ON SEQUENCE "public"."campaign_room_mapping_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."campaign_room_mapping_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."campaign_room_mapping_id_seq" TO "service_role";

GRANT ALL ON TABLE "public"."question" TO "anon";
GRANT ALL ON TABLE "public"."question" TO "authenticated";
GRANT ALL ON TABLE "public"."question" TO "service_role";

GRANT ALL ON SEQUENCE "public"."question_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."question_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."question_id_seq" TO "service_role";

GRANT ALL ON TABLE "public"."survey_response" TO "anon";
GRANT ALL ON TABLE "public"."survey_response" TO "authenticated";
GRANT ALL ON TABLE "public"."survey_response" TO "service_role";

GRANT ALL ON SEQUENCE "public"."survey_response_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."survey_response_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."survey_response_id_seq" TO "service_role";

ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";

ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";

ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";

RESET ALL;