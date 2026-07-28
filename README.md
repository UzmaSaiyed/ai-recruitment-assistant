# AI Recruitment & Document Assistant

## Day 1 Setup Instructions

### 1. Create your Supabase project
- Go to supabase.com → New Project
- Copy your Project URL and anon public key from Settings → API

### 2. Set up the database
- Open Supabase → SQL Editor
- Copy-paste everything from `schema.sql` and click "Run"
- This creates all your tables and turns on vector search

### 3. Set up your local backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Add your API keys
```bash
cp .env.example .env
```
Then open `.env` and paste in your real Supabase URL, Supabase key, and OpenAI API key.

### 5. Run the server
```bash
uvicorn main:app --reload
```

### 6. Test it
Open your browser and visit:
- http://localhost:8000/ → should say backend is running
- http://localhost:8000/test-db → should say Supabase connected
- http://localhost:8000/test-openai → should say OpenAI connected, embedding_length: 1536

If all three work, Day 1 is complete! 🎉
