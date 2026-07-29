-- Run this in Supabase SQL Editor to disable RLS on all your tables
-- (since your FastAPI backend controls all access, you don't need RLS during development)

alter table jobs disable row level security;
alter table resumes disable row level security;
alter table resume_chunks disable row level security;
alter table scores disable row level security;
alter table chat_history disable row level security;
