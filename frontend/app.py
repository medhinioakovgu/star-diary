"""
app.py – Streamlit chat interface for The Star-Interview Diary.

Sends user messages to the FastAPI /chat endpoint and displays responses
using the native st.chat_message components.
"""

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_URL = "http://localhost:8000/chat"

st.set_page_config(
    page_title="The Star-Interview Diary",
    page_icon="⭐",
    layout="centered",
)

st.title("⭐ The Star-Interview Diary")
st.caption("Your AI-powered interview coach – powered by Paparazzo")

# ---------------------------------------------------------------------------
# Session state – persist chat history across reruns
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------------
# Render existing chat history
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Handle new user input
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Type your message…"):
    # Append and display the user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build the history payload (all messages except the current one)
    history_payload = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]

    # Call the FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Paparazzo is thinking…"):
            try:
                response = requests.post(
                    API_URL,
                    json={"history": history_payload, "message": prompt},
                    timeout=60,
                )
                response.raise_for_status()
                reply = response.json().get("reply", "")
            except requests.exceptions.ConnectionError:
                reply = (
                    "⚠️ Could not connect to the backend. "
                    "Make sure the FastAPI server is running on port 8000."
                )
            except requests.exceptions.HTTPError as exc:
                reply = f"⚠️ Backend error: {exc}"
            except Exception as exc:  # noqa: BLE001
                reply = f"⚠️ Unexpected error ({type(exc).__name__}): {exc}"

        st.markdown(reply)

    # Persist the assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})
