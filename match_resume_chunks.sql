-- Run this once in Supabase SQL Editor (Day 3 setup)
-- This function does the actual vector similarity search:
-- given a query embedding, it finds the most similar resume chunks
-- for a specific job, ordered by closeness.

create or replace function match_resume_chunks (
  query_embedding vector(768),
  match_job_id uuid,
  match_count int default 5
)
returns table (
  chunk_id uuid,
  resume_id uuid,
  filename text,
  candidate_name text,
  chunk_text text,
  similarity float
)
language sql stable
as $$
  select
    resume_chunks.id as chunk_id,
    resume_chunks.resume_id,
    resumes.filename,
    resumes.candidate_name,
    resume_chunks.chunk_text,
    1 - (resume_chunks.embedding <=> query_embedding) as similarity
  from resume_chunks
  join resumes on resumes.id = resume_chunks.resume_id
  where resumes.job_id = match_job_id
  order by resume_chunks.embedding <=> query_embedding
  limit match_count;
$$;
