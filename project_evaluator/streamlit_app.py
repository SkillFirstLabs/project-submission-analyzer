"""
Streamlit demo front-end for the Project Submission AI Analyzer.

IMPORTANT: this is a UI convenience for demoing the project on video.
It is NOT the graded API — it just calls POST /analyze-submission on the
real FastAPI server below. Run the FastAPI server first:

    uvicorn main:app --reload --port 8000

Then in a second terminal:

    streamlit run streamlit_app.py
"""
import os
import json
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000/analyze-submission")

st.set_page_config(page_title="Project Submission AI Analyzer", layout="wide")
st.title("🎓 Project Submission AI Analyzer")
st.caption("Demo UI — calls the real FastAPI endpoint at " + API_URL)

with st.form("submission_form"):
    project_title = st.text_input("Project title", placeholder="Inventory Management REST API")
    project_description = st.text_area(
        "Project description (optional)",
        placeholder="A FastAPI service for managing inventory with JWT auth and Docker deployment.",
    )
    project_outcomes = st.text_area(
        "Project outcomes (one per line or numbered)",
        placeholder=(
            "1. Build a REST API for inventory management\n"
            "2. Implement user authentication and secure API access\n"
            "3. Deploy the application using Docker\n"
            "4. Apply database design and normalization principles"
        ),
        height=140,
    )
    questions_per_skill = st.slider("Questions per skill", min_value=1, max_value=6, value=2)
    zip_file = st.file_uploader("Project ZIP", type=["zip"])
    submitted = st.form_submit_button("Analyze submission")

if submitted:
    if not project_title.strip() or not project_outcomes.strip() or zip_file is None:
        st.error("project_title, project_outcomes, and a zip_file are all required.")
    else:
        with st.spinner("Analyzing submission — extracting code, matching skills, generating questions..."):
            files = {"zip_file": (zip_file.name, zip_file.getvalue(), "application/zip")}
            data = {
                "project_title": project_title,
                "project_description": project_description,
                "project_outcomes": project_outcomes,
                "questions_per_skill": questions_per_skill,
            }
            try:
                resp = requests.post(API_URL, data=data, files=files, timeout=300)
            except requests.exceptions.ConnectionError:
                st.error("Could not reach the API. Is `uvicorn main:app --port 8000` running?")
                st.stop()

        if resp.status_code != 200:
            st.error(f"API error {resp.status_code}: {resp.text}")
        else:
            result = resp.json()

            st.subheader("✅ Suggested skills")
            for s in result["suggested_skills"]:
                st.markdown(f"**{s['skill_name']}** — confidence `{s['confidence']:.2f}`")
                st.caption(s["rationale"])

            st.subheader("📝 Evaluation report")
            summary = result["evaluation_report"]["summary"]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Overall alignment", summary["overall_alignment"])
            with col2:
                st.metric("Alignment score", f"{summary['alignment_score']:.2f}")
            st.write(summary["narrative"])

            with st.expander("Outcome-by-outcome evaluation"):
                for oc in summary["outcome_evaluation"]:
                    st.markdown(f"**{oc['stated_outcome']}** — `{oc['status']}`")
                    st.write(f"Evidence: {oc['evidence']}")
                    if oc.get("gap"):
                        st.write(f"Gap: {oc['gap']}")
                    st.divider()

            col3, col4 = st.columns(2)
            with col3:
                st.markdown("**Strengths**")
                for s in summary["strengths"]:
                    st.write(f"- {s}")
            with col4:
                st.markdown("**Gaps**")
                for g in summary["gaps"]:
                    st.write(f"- {g}")

            st.subheader("❓ Interview questions per skill")
            for skill_block in result["evaluation_report"]["skills"]:
                with st.expander(skill_block["skill_name"]):
                    for q in skill_block["questions"]:
                        st.markdown(f"**[{q['question_focus']}]** {q['question_text']}")
                        st.caption("Key points: " + ", ".join(q["expected_key_points"]))

            st.subheader("Raw JSON")
            st.json(result)
