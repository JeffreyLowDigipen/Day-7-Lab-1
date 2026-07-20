import streamlit as st
from dotenv import load_dotenv

from parse import read_resume_pdf
from analyzer import (
    extract_resume_profile, extract_jd_profile, analyse_keyword_match,
    analyse_bullets, analyse_jargon, analyse_structure,
    analyse_background_fit, analyse_degree_alignment, summarise_overall, compute_overall_score,
)
from report import render_markdown

from pathlib import Path
from datetime import datetime
import json
import tempfile
import os

load_dotenv()
VALID_DEGREES = ["RTIS", "IMGD", "UXGD", "BFA"]

st.set_page_config(page_title="Resume Analyzer", layout="wide")
st.title("📄 AI Resume Analyzer")

resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
jd_text = st.text_area("Paste Job Description", height=250)
degree = st.selectbox("Select Degree", VALID_DEGREES)
run = st.button("Analyze Resume")

ATS_PASS_THRESHOLD = 60

if run:
    if not resume_file or not jd_text:
        st.error("Please upload resume and paste job description.")
        st.stop()

    # Save uploaded PDF to a temporary file for parsing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(resume_file.read())
        tmp_path = tmp.name

    try:
        resume_text = read_resume_pdf(tmp_path)
    except ValueError as exc:
        st.error(f"Could not read résumé: {exc}")
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        st.stop()

    try:
        with st.spinner("Running analyses (this may take a minute)..."):
            resume_profile = extract_resume_profile(resume_text)
            jd_profile = extract_jd_profile(jd_text)

            keyword_match = analyse_keyword_match(resume_profile, jd_profile)
            bullets = analyse_bullets(resume_profile)
            jargon = analyse_jargon(resume_profile, jd_profile)
            structure = analyse_structure(resume_text)
            background_fit = analyse_background_fit(resume_profile, jd_profile)
            degree_alignment = analyse_degree_alignment(jd_profile, degree)

            report: dict = {
                "resume_profile": resume_profile,
                "jd_profile": jd_profile,
                "keyword_match": keyword_match,
                "bullets": bullets,
                "jargon": jargon,
                "structure": structure,
                "background_fit": background_fit,
                "degree_alignment": degree_alignment,
            }

            overall_score = compute_overall_score(report)
            report["overall_score"] = overall_score
            report["passes_ats_threshold"] = overall_score >= ATS_PASS_THRESHOLD
            report["summary"] = summarise_overall(report)

            generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report["meta"] = {"generated_at": generated_at}

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            outputs_dir = Path("outputs")
            outputs_dir.mkdir(exist_ok=True)
            json_path = outputs_dir / f"match_report_{ts}.json"
            md_path = outputs_dir / f"match_report_{ts}.md"

            json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            render_markdown(report, out_path=str(md_path))
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        st.stop()
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    verdict = "PASS" if report["passes_ats_threshold"] else "FAIL"
    st.success(f"Score: {overall_score}/100  ({verdict} — {ATS_PASS_THRESHOLD}% ATS threshold)")

    st.subheader("Executive summary")
    st.markdown(report.get("summary", ""))

    st.subheader("Full report (JSON)")
    st.json(report)

    # Download buttons
    with open(json_path, "r", encoding="utf-8") as f:
        json_bytes = f.read()
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    st.download_button("Download JSON", data=json_bytes, file_name=json_path.name, mime="application/json")
    st.download_button("Download Markdown", data=md_text, file_name=md_path.name, mime="text/markdown")
