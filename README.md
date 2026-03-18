# The Star-Interview Diary

An NLP application featuring an AI-powered interview coach ("Paparazzo") built with a Streamlit frontend, a FastAPI backend, and an ML research directory for fine-tuning experiments.

## Project Structure

```
star-diary/
├── backend/          # FastAPI backend
│   ├── main.py       # API routes
│   ├── llm_engine.py # LLM logic (OpenAI / local model)
│   └── prompts.py    # System prompts
├── frontend/         # Streamlit frontend
│   └── app.py        # Chat UI
├── research/         # ML research & fine-tuning
│   ├── data/         # Training data (git-ignored)
│   ├── notebooks/    # Jupyter notebooks
│   ├── data_generation.py
│   └── train_lora.py
├── .env.example      # Environment variable template
├── requirements.txt  # Python dependencies
└── README.md
```

## Setup

1. **Clone the repo and create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your OPENAI_API_KEY and WANDB_API_KEY
   ```

## Running the Application

To run the frontend and backend simultaneously, open two terminal tabs:

**Terminal 1 – Start the FastAPI backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 – Start the Streamlit frontend:**
```bash
cd frontend
streamlit run app.py
```

The Streamlit UI will be available at `http://localhost:8501` and the API at `http://localhost:8000`.

## Research

Training scripts and notebooks live in `research/`. See `research/train_lora.py` for the LoRA fine-tuning boilerplate and `research/data_generation.py` for synthetic data generation stubs.
