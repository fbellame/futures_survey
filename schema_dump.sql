

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






CREATE OR REPLACE FUNCTION "public"."update_invitation_responded_at"("token" "text", "responded_timestamp" timestamp with time zone) RETURNS TABLE("id" "uuid", "responded_at" timestamp with time zone)
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
  -- Update the invitation and return the updated row
  RETURN QUERY
  UPDATE public.survey_invitations 
  SET 
    responded_at = responded_timestamp,
    updated_at = NOW()
  WHERE unique_token = token
  RETURNING survey_invitations.id, survey_invitations.responded_at;
END;
$$;


ALTER FUNCTION "public"."update_invitation_responded_at"("token" "text", "responded_timestamp" timestamp with time zone) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_updated_at_column"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_updated_at_column"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."answer" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "survey_submission_id" "uuid" NOT NULL,
    "question_id" bigint NOT NULL,
    "answer_text" "text" NOT NULL,
    "answered_at" timestamp with time zone DEFAULT "now"(),
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."answer" OWNER TO "postgres";


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
    "user_id" "uuid",
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



CREATE TABLE IF NOT EXISTS "public"."survey_invitations" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "campaign_id" bigint NOT NULL,
    "email" "text" NOT NULL,
    "unique_token" "text" DEFAULT "encode"("extensions"."gen_random_bytes"(32), 'base64'::"text") NOT NULL,
    "qr_code_url" "text",
    "sent_at" timestamp with time zone,
    "responded_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "user_id" "uuid"
);


ALTER TABLE "public"."survey_invitations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."survey_submissions" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "campaign_id" bigint NOT NULL,
    "full_name" "text",
    "email" "text",
    "geography" "text",
    "occupation" "text",
    "phone_number" "text",
    "room_name" "text" NOT NULL,
    "invitation_token" "text",
    "s3_recording_url" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "call_timestamp" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."survey_submissions" OWNER TO "postgres";


ALTER TABLE ONLY "public"."campaign" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."campaign_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."campaign_room_mapping" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."campaign_room_mapping_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."question" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."question_id_seq"'::"regclass");



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



ALTER TABLE ONLY "public"."survey_invitations"
    ADD CONSTRAINT "survey_invitations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."survey_invitations"
    ADD CONSTRAINT "survey_invitations_unique_token_key" UNIQUE ("unique_token");



ALTER TABLE ONLY "public"."survey_submissions"
    ADD CONSTRAINT "survey_submissions_pkey" PRIMARY KEY ("id");



CREATE INDEX "idx_campaign_id" ON "public"."question" USING "btree" ("campaign_id");



CREATE INDEX "idx_campaign_room_mapping_campaign_id" ON "public"."campaign_room_mapping" USING "btree" ("campaign_id");



CREATE INDEX "idx_campaign_room_mapping_pattern" ON "public"."campaign_room_mapping" USING "btree" ("room_pattern");



CREATE INDEX "idx_campaign_uri" ON "public"."campaign" USING "btree" ("campaign_uri");



CREATE INDEX "idx_survey_invitations_campaign_id" ON "public"."survey_invitations" USING "btree" ("campaign_id");



CREATE INDEX "idx_survey_invitations_email" ON "public"."survey_invitations" USING "btree" ("email");



CREATE INDEX "idx_survey_invitations_token" ON "public"."survey_invitations" USING "btree" ("unique_token");



CREATE OR REPLACE TRIGGER "update_answer_updated_at" BEFORE UPDATE ON "public"."answer" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_survey_invitations_updated_at" BEFORE UPDATE ON "public"."survey_invitations" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_survey_submissions_updated_at" BEFORE UPDATE ON "public"."survey_submissions" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



ALTER TABLE ONLY "public"."answer"
    ADD CONSTRAINT "answer_question_id_fkey" FOREIGN KEY ("question_id") REFERENCES "public"."question"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."answer"
    ADD CONSTRAINT "answer_survey_submission_id_fkey" FOREIGN KEY ("survey_submission_id") REFERENCES "public"."survey_submissions"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."campaign_room_mapping"
    ADD CONSTRAINT "campaign_room_mapping_campaign_id_fkey" FOREIGN KEY ("campaign_id") REFERENCES "public"."campaign"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."campaign"
    ADD CONSTRAINT "campaign_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."question"
    ADD CONSTRAINT "question_campaign_id_fkey" FOREIGN KEY ("campaign_id") REFERENCES "public"."campaign"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."survey_invitations"
    ADD CONSTRAINT "survey_invitations_campaign_id_fkey" FOREIGN KEY ("campaign_id") REFERENCES "public"."campaign"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."survey_invitations"
    ADD CONSTRAINT "survey_invitations_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



CREATE POLICY "Allow anonymous delete access to campaign_room_mapping" ON "public"."campaign_room_mapping" FOR DELETE USING (true);



CREATE POLICY "Allow anonymous delete access to question" ON "public"."question" FOR DELETE USING (true);



CREATE POLICY "Allow anonymous insert access to campaign_room_mapping" ON "public"."campaign_room_mapping" FOR INSERT WITH CHECK (true);



CREATE POLICY "Allow anonymous insert access to question" ON "public"."question" FOR INSERT WITH CHECK (true);



CREATE POLICY "Allow anonymous read access to campaign_room_mapping" ON "public"."campaign_room_mapping" FOR SELECT USING (true);



CREATE POLICY "Allow anonymous read access to question" ON "public"."question" FOR SELECT USING (true);



CREATE POLICY "Allow anonymous read for invitation token validation" ON "public"."survey_invitations" FOR SELECT USING (true);



CREATE POLICY "Allow anonymous read for survey campaigns" ON "public"."campaign" FOR SELECT USING (true);



CREATE POLICY "Allow anonymous read for token validation" ON "public"."survey_invitations" FOR SELECT TO "anon" USING (true);



CREATE POLICY "Allow anonymous update access to campaign_room_mapping" ON "public"."campaign_room_mapping" FOR UPDATE USING (true);



CREATE POLICY "Allow service role to select campaign room mappings" ON "public"."campaign_room_mapping" FOR SELECT TO "service_role" USING (true);



CREATE POLICY "Allow service role to select campaigns" ON "public"."campaign" FOR SELECT TO "service_role" USING (true);



CREATE POLICY "Allow service role to select questions" ON "public"."question" FOR SELECT TO "service_role" USING (true);



CREATE POLICY "Anyone can submit answers" ON "public"."answer" USING (true) WITH CHECK (true);



CREATE POLICY "Anyone can submit survey data" ON "public"."survey_submissions" USING (true) WITH CHECK (true);



CREATE POLICY "Users can create survey invitations" ON "public"."survey_invitations" FOR INSERT TO "authenticated" WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can create their own campaigns" ON "public"."campaign" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can delete their own campaigns" ON "public"."campaign" FOR DELETE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can delete their own invitations" ON "public"."survey_invitations" FOR DELETE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can update their own campaigns" ON "public"."campaign" FOR UPDATE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can update their own invitations" ON "public"."survey_invitations" FOR UPDATE TO "authenticated" USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view their own campaigns" ON "public"."campaign" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view their own invitations" ON "public"."survey_invitations" FOR SELECT TO "authenticated" USING (("auth"."uid"() = "user_id"));



ALTER TABLE "public"."answer" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."campaign" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."campaign_room_mapping" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."question" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."survey_invitations" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."survey_submissions" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";

























































































































































GRANT ALL ON FUNCTION "public"."update_invitation_responded_at"("token" "text", "responded_timestamp" timestamp with time zone) TO "anon";
GRANT ALL ON FUNCTION "public"."update_invitation_responded_at"("token" "text", "responded_timestamp" timestamp with time zone) TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_invitation_responded_at"("token" "text", "responded_timestamp" timestamp with time zone) TO "service_role";



GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "service_role";


















GRANT ALL ON TABLE "public"."answer" TO "anon";
GRANT ALL ON TABLE "public"."answer" TO "authenticated";
GRANT ALL ON TABLE "public"."answer" TO "service_role";



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



GRANT ALL ON TABLE "public"."survey_invitations" TO "anon";
GRANT ALL ON TABLE "public"."survey_invitations" TO "authenticated";
GRANT ALL ON TABLE "public"."survey_invitations" TO "service_role";



GRANT ALL ON TABLE "public"."survey_submissions" TO "anon";
GRANT ALL ON TABLE "public"."survey_submissions" TO "authenticated";
GRANT ALL ON TABLE "public"."survey_submissions" TO "service_role";









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
