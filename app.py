import streamlit as st
import json
import time
import pandas as pd
import random
import os
from datetime import datetime

st.set_page_config(page_title="Student Learning Twin", page_icon="🧠")

LOG_PATH = "user_logs.csv"

# =============== LOAD QUESTIONS =================
@st.cache_data
def load_questions():
    with open("questions.json", "r") as f:
        return json.load(f)

questions = load_questions()

# Group by difficulty
questions_by_diff = {"easy": [], "medium": [], "hard": []}
for q in questions:
    questions_by_diff[q["difficulty"]].append(q)

# =============== SESSION STATE =================
if "current_question" not in st.session_state:
    st.session_state.current_question = None

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "logs" not in st.session_state:
    st.session_state.logs = []  # session-only logs

if "user" not in st.session_state:
    st.session_state.user = ""

# =============== HELPERS =================
def get_last_accuracy(n=3):
    """Compute accuracy from the last n questions in THIS SESSION."""
    logs = st.session_state.logs
    if not logs:
        return None
    last = logs[-n:]
    correct_count = sum(1 for x in last if x["correct"] is True)
    return correct_count / len(last)

def pick_question():
    """Pick next question based on recent performance and avoid infinite repeats."""
    acc = get_last_accuracy()

    if acc is None:
        level = "medium"
    elif acc >= 0.8:
        level = "hard"
    elif acc <= 0.5:
        level = "easy"
    else:
        level = "medium"

    pool = questions_by_diff[level]

    # avoid repeating questions from THIS session
    answered_ids = [x["question_id"] for x in st.session_state.logs]
    clean_pool = [q for q in pool if q["id"] not in answered_ids]

    # if nothing left at this difficulty, try ANY difficulty that hasn't been asked yet
    if not clean_pool:
        clean_pool = [q for q in questions if q["id"] not in answered_ids]

    # if still nothing, we are out of questions
    if not clean_pool:
        return None

    return random.choice(clean_pool)

def start_question():
    st.session_state.start_time = time.time()

def load_all_logs():
    if os.path.exists(LOG_PATH):
        df = pd.read_csv(LOG_PATH)

        # Case 1: already have correct_numeric -> make sure it's numeric
        if "correct_numeric" in df.columns:
            df["correct_numeric"] = pd.to_numeric(df["correct_numeric"], errors="coerce").fillna(0).astype(int)

        # Case 2: old format with 'correct' as True/False or 'True'/'False'
        elif "correct" in df.columns:
            def to_num(x):
                s = str(x).strip().lower()
                if s in ["true", "1", "yes"]:
                    return 1
                if s in ["false", "0", "no"]:
                    return 0
                return 0  # default if weird value
            df["correct_numeric"] = df["correct"].map(to_num).astype(int)

        # Case 3: nothing there, just create the column
        else:
            df["correct_numeric"] = 0

        return df
    else:
        cols = ["user", "question_id", "topic", "chapter", "difficulty",
                "correct_numeric", "time_taken", "timestamp"]
        return pd.DataFrame(columns=cols)

def append_log_row(row_dict):
    new_row_df = pd.DataFrame([row_dict])
    if os.path.exists(LOG_PATH):
        new_row_df.to_csv(LOG_PATH, mode="a", header=False, index=False)
    else:
        new_row_df.to_csv(LOG_PATH, index=False)

# =============== UI: USER ID =================
st.title("🧠 Student Learning Twin")

st.write("This system is learning how **you** learn over time, not just in this session.")

user_input = st.text_input(
    "Enter your name or ID to build your personal twin:",
    value=st.session_state.user
)

if user_input:
    st.session_state.user = user_input.strip()

if not st.session_state.user:
    st.warning("Please enter a name or ID to continue.")
    st.stop()

st.info(f"Current student: **{st.session_state.user}**")

# =============== QUESTION UI =================
# pick first question if needed
if st.session_state.current_question is None:
    st.session_state.current_question = pick_question()

q = st.session_state.current_question

if q is None:
    st.success("You’ve answered all available questions for now 🎉")
else:
    if st.session_state.start_time is None:
        start_question()

    st.subheader(q["question"])
    choice = st.radio("Select an answer:", q["options"], index=None)

    if st.button("Submit Answer", disabled=(choice is None)):

        end_time = time.time()
        time_taken = round(end_time - st.session_state.start_time, 2)

        is_correct = (q["options"].index(choice) == q["answer"])

        # log in SESSION (keep correct as bool here)
        session_log_entry = {
            "question_id": q["id"],
            "topic": q["topic"],
            "chapter": q["chapter"],
            "difficulty": q["difficulty"],
            "correct": is_correct,
            "time_taken": time_taken
        }
        st.session_state.logs.append(session_log_entry)

        # log in CSV (store correct as numeric 0/1)
        persistent_entry = {
            "user": st.session_state.user,
            "question_id": q["id"],
            "topic": q["topic"],
            "chapter": q["chapter"],
            "difficulty": q["difficulty"],
            "correct_numeric": int(is_correct),
            "time_taken": time_taken,
            "timestamp": datetime.now().isoformat(timespec="seconds")
        }
        append_log_row(persistent_entry)

        st.success("✅ Correct!" if is_correct else "❌ Wrong")
        st.info(f"Time taken: {time_taken} seconds")

        # prepare next question
        st.session_state.current_question = pick_question()
        st.session_state.start_time = None

        st.rerun()

st.divider()
st.header("📊 Your Learning Twin Analysis")

# =============== ANALYTICS =================
all_logs = load_all_logs()
user_logs = all_logs[all_logs["user"] == st.session_state.user].copy()

# Also merge current session logs (if not yet persisted fully)
if st.session_state.logs:
    session_df = pd.DataFrame(st.session_state.logs)
    if not session_df.empty:
        session_df["user"] = st.session_state.user
        session_df["correct_numeric"] = session_df["correct"].apply(lambda x: 1 if x else 0)
        user_logs = pd.concat([user_logs, session_df], ignore_index=True)

if user_logs.empty:
    st.info("No history yet. Answer a few questions to build your twin.")
else:
    # Make sure correct_numeric is numeric
    user_logs["correct_numeric"] = (
    user_logs["correct_numeric"]
    .astype(str)
    .str.lower()
    .map({"1": 1, "0": 0, "true": 1, "false": 0})
    .fillna(0)
    .astype(int)
)

    st.subheader("Accuracy by Topic")
    topic_acc = user_logs.groupby("topic")["correct_numeric"].mean()
    st.dataframe(topic_acc)
    st.bar_chart(topic_acc)

    st.subheader("Accuracy by Chapter")
    chapter_acc = user_logs.groupby("chapter")["correct_numeric"].mean()
    st.dataframe(chapter_acc)
    st.bar_chart(chapter_acc)

    st.subheader("Accuracy by Difficulty")
    diff_acc = user_logs.groupby("difficulty")["correct_numeric"].mean()
    st.dataframe(diff_acc)
    st.bar_chart(diff_acc)

    avg_time = user_logs["time_taken"].mean()
    st.metric("Average time per question (sec)", f"{avg_time:.2f}")

    st.subheader("⏱ Time per Question Trend")
    st.line_chart(user_logs["time_taken"])

    # Weakest chapter (lowest accuracy)
    weakest_chapter = chapter_acc.sort_values().index[0]

    st.subheader("⚠️ Weakest Area Detected")
    st.write(f"Your weakest chapter so far appears to be: **{weakest_chapter}**")

    st.subheader("✅ Suggested Learning Plan")
    st.markdown(f"""
    Based on your performance so far:

    - Focus extra on **{weakest_chapter}**
    - Revise theory and solve at least 10 problems from this chapter
    - Start with **easy** and **medium** questions, then move to **hard**
    - Revisit your mistakes and check where you spent too much time
    """)