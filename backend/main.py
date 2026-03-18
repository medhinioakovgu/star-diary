"""
main.py – FastAPI entry-point for the Star-Interview Diary backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llm_engine import generate_paparazzo_reply

app = FastAPI(title="Star-Interview Diary API", version="0.1.0")

# ---------------------------------------------------------------------------
# CORS – allow the Streamlit dev server (and any localhost origin) to call
# the API during local development.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Streamlit dev server
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        # Expo web / React Native web (metro bundler default ports)
        "http://localhost:8081",
        "http://localhost:19006",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:19006",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    history: list[ChatMessage] = []
    message: str


class ChatResponse(BaseModel):
    reply: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
def health_check():
    """Simple liveness probe."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Accept a user message (with optional prior chat history) and return
    Paparazzo's reply.
    """
    history = [msg.model_dump() for msg in request.history]
    reply = generate_paparazzo_reply(
        chat_history=history,
        user_message=request.message,
    )
    return ChatResponse(reply=reply)
