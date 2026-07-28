"""
Day 1 goal: prove that FastAPI + Supabase + Gemini are all connected and working.
Nothing fancy yet — just test endpoints.
"""

import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from supabase import create_client
import google.generativeai as genai
import fitz  # PyMuPDF

# Load variables from your .env file
load_dotenv()

app = FastAPI(title="AI Recruitment Assistant")

# --- Connect to Supabase ---
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# --- Connect to Gemini ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Opens a PDF from raw bytes and pulls out all readable text."""
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    """
    Splits long text into overlapping chunks so each chunk is small enough
    to embed well and search accurately. Overlap helps avoid cutting a
    sentence/skill in half between two chunks.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def get_embedding(text: str) -> list[float]:
    """Calls Gemini to turn a piece of text into a 768-dimension vector."""
    response = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        output_dimensionality=768
    )
    return response["embedding"]


@app.get("/")
def home():
    """Just checks the server is running."""
    return {"message": "AI Recruitment Assistant backend is running!"}


@app.get("/test-db")
def test_db():
    """Checks that we can talk to Supabase."""
    try:
        result = supabase.table("jobs").select("*").limit(1).execute()
        return {"status": "success", "message": "Supabase connected!", "data": result.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/test-gemini")
def test_gemini():
    """Checks that we can talk to Gemini (does a tiny embedding call)."""
    try:
        response = genai.embed_content(
            model="models/gemini-embedding-001",
            content="This is a test sentence.",
            output_dimensionality=768  # keeps vectors small enough for pgvector to index
        )
        vector_length = len(response["embedding"])
        return {
            "status": "success",
            "message": "Gemini connected!",
            "embedding_length": vector_length  # should print 768
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/test-gemini-chat")
def test_gemini_chat():
    """Checks that the Gemini chat/generation model works too."""
    try:
        model = genai.GenerativeModel("gemini-3.6-flash")
        response = model.generate_content("Say hello in one short sentence.")
        return {"status": "success", "message": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================
# DAY 2: Upload endpoints
# ============================================================

@app.post("/upload-job")
async def upload_job(title: str = Form(...), file: UploadFile = File(...)):
    """
    Upload a Job Description PDF.
    'title' is just a label you choose, e.g. "AI Intern - E2M"
    'file' is the JD PDF itself.
    """
    try:
        file_bytes = await file.read()
        jd_text = extract_text_from_pdf(file_bytes)

        if not jd_text:
            return {"status": "error", "message": "Could not extract any text from this PDF."}

        result = supabase.table("jobs").insert({
            "title": title,
            "raw_text": jd_text
        }).execute()

        job_id = result.data[0]["id"]
        return {
            "status": "success",
            "job_id": job_id,
            "extracted_characters": len(jd_text)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/upload-resumes")
async def upload_resumes(job_id: str = Form(...), files: list[UploadFile] = File(...)):
    """
    Upload a batch of resume PDFs, all linked to one job_id.
    You get the job_id back from the /upload-job response above.
    """
    results = []
    for file in files:
        try:
            file_bytes = await file.read()
            resume_text = extract_text_from_pdf(file_bytes)

            if not resume_text:
                results.append({"filename": file.filename, "status": "error", "message": "No text extracted"})
                continue

            result = supabase.table("resumes").insert({
                "job_id": job_id,
                "filename": file.filename,
                "candidate_name": file.filename.replace(".pdf", ""),  # placeholder, we'll improve this later
                "raw_text": resume_text
            }).execute()

            results.append({
                "filename": file.filename,
                "status": "success",
                "resume_id": result.data[0]["id"],
                "extracted_characters": len(resume_text)
            })
        except Exception as e:
            results.append({"filename": file.filename, "status": "error", "message": str(e)})

    return {"uploaded": results}


@app.get("/jobs")
def list_jobs():
    """See all uploaded job descriptions (for quick testing)."""
    try:
        result = supabase.table("jobs").select("id, title, created_at").execute()
        return {"status": "success", "jobs": result.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/resumes/{job_id}")
def list_resumes(job_id: str):
    """See all resumes uploaded for a specific job (for quick testing)."""
    try:
        result = supabase.table("resumes").select("id, filename, candidate_name, created_at").eq("job_id", job_id).execute()
        return {"status": "success", "resumes": result.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================
# DAY 3: Embeddings & Vector Search
# ============================================================

@app.post("/embed-job/{job_id}")
def embed_job(job_id: str):
    """
    Generates an embedding for the JD itself and saves it to the jobs table.
    Run this once per job, after uploading it.
    """
    try:
        job = supabase.table("jobs").select("raw_text").eq("id", job_id).execute()
        if not job.data:
            return {"status": "error", "message": "Job not found"}

        jd_text = job.data[0]["raw_text"]
        embedding = get_embedding(jd_text)

        supabase.table("jobs").update({"embedding": embedding}).eq("id", job_id).execute()

        return {"status": "success", "message": "Job embedded successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/embed-resumes/{job_id}")
def embed_resumes(job_id: str):
    """
    For every resume linked to this job:
    1. Split the resume text into chunks
    2. Generate an embedding for each chunk
    3. Save each chunk + embedding into resume_chunks

    Run this once after uploading resumes, before using search or scoring.
    """
    try:
        resumes = supabase.table("resumes").select("id, filename, raw_text").eq("job_id", job_id).execute()

        if not resumes.data:
            return {"status": "error", "message": "No resumes found for this job"}

        results = []
        for resume in resumes.data:
            chunks = chunk_text(resume["raw_text"])
            chunks_saved = 0

            for chunk in chunks:
                embedding = get_embedding(chunk)
                supabase.table("resume_chunks").insert({
                    "resume_id": resume["id"],
                    "chunk_text": chunk,
                    "embedding": embedding
                }).execute()
                chunks_saved += 1

            results.append({
                "filename": resume["filename"],
                "chunks_saved": chunks_saved
            })

        return {"status": "success", "resumes_processed": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/search")
def search(job_id: str, query: str, top_k: int = 5):
    """
    Test endpoint: given a natural-language question, finds the most
    relevant resume chunks using vector similarity search.

    Example: /search?job_id=xxx&query=who has 3 years of React experience
    """
    try:
        query_embedding = get_embedding(query)

        # This calls a Postgres function we need to create once in Supabase (see match_resume_chunks.sql)
        result = supabase.rpc("match_resume_chunks", {
            "query_embedding": query_embedding,
            "match_job_id": job_id,
            "match_count": top_k
        }).execute()

        return {"status": "success", "results": result.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}