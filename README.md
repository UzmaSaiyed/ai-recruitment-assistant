# AI Recruitment & Document Assistant

An AI-powered recruitment platform that parses job descriptions and resumes, scores and ranks candidates using an LLM, and lets recruiters query candidates in natural language through a RAG-based chat assistant. Also generates a one-click shortlist report.

## Live Demo

- **Dashboard:** https://ai-recruitment-assistant-project.streamlit.app/
- **Backend API docs:** https://ai-recruitment-assistant-537j.onrender.com/docs


## Features

- Upload a Job Description + a batch of resumes (PDF)
- Automatic text extraction and chunking
- Vector embeddings + similarity search (pgvector)
- LLM-based candidate scoring with structured, explainable JSON output (score, matched skills, gaps, reasoning)
- RAG chat assistant — ask natural-language questions about candidates, answers are grounded in the actual resume content with source attribution
- One-click automated shortlist report generation
- Simple Streamlit dashboard for the full workflow

## Tech Stack

- **Backend:** FastAPI
- **Database:** Supabase (Postgres + pgvector)
- **LLM/Embeddings:** Google Gemini API
- **Frontend:** Streamlit
- **Deployment:** Render (backend), Streamlit Community Cloud (frontend)

## Project Structure

```
ai-recruitment-assistant/
  backend/
    main.py
    requirements.txt
    .env
  frontend/
    app.py
    requirements.txt
  schema.sql
  match_resume_chunks.sql
  disable_rls.sql
```

## Running Locally

### 1. Set up Supabase
- Create a project at supabase.com
- Copy your Project URL and anon public key from Settings → API
- Open the SQL Editor and run everything in `schema.sql`, then `match_resume_chunks.sql`

### 2. Set up the backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```
Fill in your `SUPABASE_URL`, `SUPABASE_KEY`, and `GEMINI_API_KEY` in `.env`.

```bash
uvicorn main:app --reload
```
Visit `http://localhost:8000/docs` to test the API directly.

### 3. Set up the frontend
```bash
cd frontend
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Visit `http://localhost:8501` for the dashboard (make sure `BACKEND_URL` in `app.py` points to your running backend).

## How It Works

1. Upload a Job Description and a batch of resumes (PDF)
2. The backend extracts text, generates vector embeddings, and stores everything in Supabase
3. Each resume is scored against the JD using Gemini, producing a structured score, matched skills, gaps, and reasoning
4. Ask the chat assistant questions about the candidate pool — answers are retrieved from the actual resume content, not guessed
5. Generate a clean, written shortlist report summarizing the top candidates
