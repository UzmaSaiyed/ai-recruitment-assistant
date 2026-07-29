"""
Streamlit dashboard for the AI Recruitment Assistant.
This talks to your FastAPI backend (main.py) which must be running
at http://localhost:8000 for this to work.
"""

import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Recruitment Assistant", layout="wide")
st.title("AI Recruitment & Document Assistant")

# Keep track of the current job_id across the app
if "job_id" not in st.session_state:
    st.session_state.job_id = None

tab_upload, tab_shortlist, tab_chat, tab_report = st.tabs(
    ["Upload", "Shortlist", "Chat", "Report"]
)

# ---------------- Upload tab ----------------
with tab_upload:
    st.subheader("1. Upload Job Description")
    job_title = st.text_input("Job title", placeholder="e.g. AI Intern - E2M")
    jd_file = st.file_uploader("Upload JD (PDF)", type=["pdf"], key="jd")

    if st.button("Upload Job Description"):
        if job_title and jd_file:
            files = {"file": (jd_file.name, jd_file.getvalue(), "application/pdf")}
            data = {"title": job_title}
            response = requests.post(f"{BACKEND_URL}/upload-job", files=files, data=data)
            result = response.json()
            if result.get("status") == "success":
                st.session_state.job_id = result["job_id"]
                st.success(f"Job uploaded! Job ID: {result['job_id']}")
            else:
                st.error(result.get("message"))
        else:
            st.warning("Please enter a job title and choose a PDF file.")

    st.divider()
    st.subheader("2. Upload Resumes")
    resume_files = st.file_uploader(
        "Upload resumes (PDF, multiple allowed)", type=["pdf"], accept_multiple_files=True, key="resumes"
    )

    if st.button("Upload Resumes"):
        if not st.session_state.job_id:
            st.warning("Please upload a Job Description first.")
        elif not resume_files:
            st.warning("Please choose at least one resume PDF.")
        else:
            files = [("files", (f.name, f.getvalue(), "application/pdf")) for f in resume_files]
            data = {"job_id": st.session_state.job_id}
            response = requests.post(f"{BACKEND_URL}/upload-resumes", files=files, data=data)
            st.json(response.json())

    st.divider()
    st.subheader("3. Process (embed + score)")
    if st.button("Embed Resumes"):
        if st.session_state.job_id:
            response = requests.post(f"{BACKEND_URL}/embed-resumes/{st.session_state.job_id}")
            st.json(response.json())
        else:
            st.warning("Upload a job first.")

    if st.button("Score Resumes"):
        if st.session_state.job_id:
            response = requests.post(f"{BACKEND_URL}/score-resumes/{st.session_state.job_id}")
            st.json(response.json())
        else:
            st.warning("Upload a job first.")

# ---------------- Shortlist tab ----------------
with tab_shortlist:
    st.subheader("Ranked Candidates")
    if st.session_state.job_id:
        if st.button("Refresh Shortlist"):
            response = requests.get(f"{BACKEND_URL}/ranked/{st.session_state.job_id}")
            result = response.json()
            if result.get("status") == "success":
                for candidate in result["ranked_candidates"]:
                    name = candidate["resumes"]["candidate_name"]
                    with st.expander(f"{name} — Score: {candidate['score']}/100"):
                        st.write("**Matched skills:**", ", ".join(candidate["matched_skills"]))
                        st.write("**Gaps:**", ", ".join(candidate["gaps"]))
                        st.write("**Reasoning:**", candidate["reasoning"])
            else:
                st.error(result.get("message"))
    else:
        st.info("Upload a job and score resumes first.")

# ---------------- Chat tab ----------------
with tab_chat:
    st.subheader("Ask about your candidates")
    question = st.text_input("Your question", placeholder="e.g. Who has 3+ years of React experience?")
    if st.button("Ask"):
        if st.session_state.job_id and question:
            data = {"job_id": st.session_state.job_id, "question": question}
            response = requests.post(f"{BACKEND_URL}/chat", data=data)
            result = response.json()
            if result.get("status") == "success":
                st.write(result["answer"])
                st.caption("Sources: " + ", ".join(result["sources"]))
            else:
                st.error(result.get("message"))
        else:
            st.warning("Upload a job and enter a question first.")

# ---------------- Report tab ----------------
with tab_report:
    st.subheader("Shortlist Report")
    if st.button("Generate Report"):
        if st.session_state.job_id:
            response = requests.get(f"{BACKEND_URL}/generate-report/{st.session_state.job_id}")
            result = response.json()
            if result.get("status") == "success":
                st.markdown(result["report"])
            else:
                st.error(result.get("message"))
        else:
            st.warning("Upload a job first.")
