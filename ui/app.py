import streamlit as st
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'survey.db')

def get_calls():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, phone_number, campaign_id, call_timestamp, s3_recording_url FROM call ORDER BY call_timestamp DESC")
        return cur.fetchall()

def get_answers_for_call(call_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT q.question_order, q.question_text, a.answer_text, a.answered_at
            FROM answer a
            JOIN question q ON a.question_id = q.id
            WHERE a.call_id = ?
            ORDER BY q.question_order
        ''', (call_id,))
        return cur.fetchall()

def main():
    st.title("Survey Calls Viewer")
    calls = get_calls()
    if not calls:
        st.info("No calls found in the database.")
        return
    call_options = [f"Call #{c[0]} | {c[1]} | {c[3]}" for c in calls]
    selected = st.selectbox("Select a call to view details:", options=call_options)
    selected_idx = call_options.index(selected)
    call = calls[selected_idx]
    st.subheader(f"Call Details (ID: {call[0]})")
    st.write(f"**Phone Number:** {call[1]}")
    st.write(f"**Campaign ID:** {call[2]}")
    st.write(f"**Timestamp:** {call[3]}")
    st.write(f"**S3 Recording URL:** {call[4] if call[4] else 'N/A'}")
    st.markdown("---")
    st.subheader("Answers")
    answers = get_answers_for_call(call[0])
    if not answers:
        st.info("No answers recorded for this call.")
    else:
        for q_order, q_text, a_text, a_time in answers:
            st.markdown(f"**Q{q_order}: {q_text}**")
            st.write(f"Answer: {a_text}")
            st.write(f"Answered at: {a_time}")
            st.markdown("---")

if __name__ == "__main__":
    main() 