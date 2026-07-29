-- Run this entire file in Supabase SQL Editor (Day 1, Step 2)

-- 1. Enable the pgvector extension (lets Postgres store & search embeddings)
create extension if not exists vector;

-- 2. Table to store each Job Description you upload
create table jobs (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    raw_text text not null,
    embedding vector(768),  -- gemini-embedding-001 truncated to 768 dimensions (indexable + efficient)
    created_at timestamp default now()
);

-- 3. Table to store each uploaded resume (one row per resume file)
create table resumes (
    id uuid primary key default gen_random_uuid(),
    job_id uuid references jobs(id) on delete cascade,
    candidate_name text,
    filename text not null,
    raw_text text not null,
    created_at timestamp default now()
);

-- 4. Table to store resume TEXT CHUNKS + their embeddings (for RAG search)
-- We split each resume into smaller chunks (e.g. by section) for better retrieval
create table resume_chunks (
    id uuid primary key default gen_random_uuid(),
    resume_id uuid references resumes(id) on delete cascade,
    chunk_text text not null,
    embedding vector(768),  -- gemini-embedding-001 truncated to 768 dimensions (indexable + efficient)
    created_at timestamp default now()
);

-- 5. Table to store LLM scoring results for each resume against a job
create table scores (
    id uuid primary key default gen_random_uuid(),
    job_id uuid references jobs(id) on delete cascade,
    resume_id uuid references resumes(id) on delete cascade,
    score numeric,               -- e.g. 0-100
    matched_skills jsonb,        -- list of matched skills
    gaps jsonb,                  -- list of missing skills
    reasoning text,               -- LLM's explanation
    created_at timestamp default now()
);

-- 6. Table to store chat history for the RAG assistant (optional but useful)
create table chat_history (
    id uuid primary key default gen_random_uuid(),
    job_id uuid references jobs(id) on delete cascade,
    question text not null,
    answer text not null,
    created_at timestamp default now()
);

-- 7. Index to make vector similarity search fast (important once you have many resumes)
create index on resume_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);
