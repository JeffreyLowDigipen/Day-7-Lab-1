"""
prompts.py — all 8 system prompts used by analyzer.py.

Task 3 of the lab (Track A).
Study material references:
  §3.3 Schema-First Prompt Design
  §6.1 Extraction Prompts
  §6.2 Evaluation Prompts
  §6.3 Feedback-Only Principle

Every prompt must follow ICCO structure:
  Instruction  — what the model must do
  Context      — relevant background (rubric description, schema description)
  Constraints  — rules the model must not break
  Output       — the exact JSON schema expected

Every prompt (except OVERALL_SUMMARY_PROMPT) must end with:
  "Output ONLY a valid JSON object matching the schema above. No prose. No
  markdown fences. No commentary. Never rewrite or generate résumé content."

Temperature guidance (set in the ask_json() call in analyzer.py):
  Extraction prompts (RESUME_PROFILE, JD_PROFILE): 0.0
  Evaluation prompts (KEYWORD_MATCH, BULLET_QUALITY, JARGON, STRUCTURE, BACKGROUND_FIT): 0.2–0.3
  OVERALL_SUMMARY_PROMPT: 0.3
"""


# ---------------------------------------------------------------------------
# Extraction prompts
# ---------------------------------------------------------------------------

# Purpose: extract a structured candidate profile from plain résumé text.
# Input to ask_json(): system=RESUME_PROFILE_PROMPT, user="RÉSUMÉ TEXT:\n\n{text}"
# Expected output schema — all fields required; arrays may be empty:
# {
#   "name": "string",
#   "contact": {
#     "email": "string", "phone": "string", "linkedin": "string",
#     "github": "string", "portfolio": "string"
#   },
#   "summary": "string",
#   "education": [{"school": "string", "degree": "string",
#                  "graduation_date": "string", "courses": ["string"]}],
#   "projects":  [{"title": "string", "date": "string", "bullets": ["string"]}],
#   "experience":[{"title": "string", "company": "string",
#                  "date": "string", "bullets": ["string"]}],
#   "skills": {
#     "languages": ["string"], "frameworks": ["string"], "tools": ["string"],
#     "concepts": ["string"], "platforms": ["string"]
#   }
# }
RESUME_PROFILE_PROMPT = """
Instruction: Extract a structured candidate profile from the provided résumé text.

Context: You are helping build an ATS-focused résumé analysis pipeline. The output must match the schema below exactly and should reflect only information explicitly present in the résumé.

Constraints: Do not invent facts, titles, dates, skills, or contact details. Use empty strings and empty arrays when information is missing. Preserve the original wording where practical. Never rewrite or generate résumé content. Do not add commentary or explanations.

Output: Return a JSON object with this schema:
{
  \"name\": \"string\",
  \"contact\": {
    \"email\": \"string\", \"phone\": \"string\", \"linkedin\": \"string\",
    \"github\": \"string\", \"portfolio\": \"string\"
  },
  \"summary\": \"string\",
  \"education\": [{\"school\": \"string\", \"degree\": \"string\",
                   \"graduation_date\": \"string\", \"courses\": [\"string\"]}],
  \"projects\":  [{\"title\": \"string\", \"date\": \"string\", \"bullets\": [\"string\"]}],
  \"experience\":[{\"title\": \"string\", \"company\": \"string\",
                  \"date\": \"string\", \"bullets\": [\"string\"]}],
  \"skills\": {
    \"languages\": [\"string\"], \"frameworks\": [\"string\"], \"tools\": [\"string\"],
    \"concepts\": [\"string\"], \"platforms\": [\"string\"]
  }
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# Purpose: extract a structured JD profile from free-form job posting text.
# Input to ask_json(): system=JD_PROFILE_PROMPT, user="JOB DESCRIPTION TEXT:\n\n{text}"
# Expected output schema — all fields required; arrays may be empty:
# {
#   "job_title": "string",
#   "company": "string",
#   "location": "string",
#   "experience_level": "string",
#   "required_skills": ["string"],
#   "preferred_skills": ["string"],
#   "tools_technologies": ["string"],
#   "responsibilities": ["string"],
#   "soft_skills": ["string"],
#   "buzzwords": ["string"],
#   "deal_breakers": ["string"]
# }
JD_PROFILE_PROMPT = """
Instruction: Extract a structured profile from the provided job description text.

Context: You are helping analyze how well a résumé matches a target role. The output must match the schema below exactly and should reflect only information explicitly present in the job description.

Constraints: Do not invent company names, locations, titles, tools, responsibilities, or skills. Use empty strings and empty arrays when information is missing. Preserve the original wording where practical. Never rewrite or generate résumé content. Do not add commentary or explanations.

Output: Return a JSON object with this schema:
{
  \"job_title\": \"string\",
  \"company\": \"string\",
  \"location\": \"string\",
  \"experience_level\": \"string\",
  \"required_skills\": [\"string\"],
  \"preferred_skills\": [\"string\"],
  \"tools_technologies\": [\"string\"],
  \"responsibilities\": [\"string\"],
  \"soft_skills\": [\"string\"],
  \"buzzwords\": [\"string\"],
  \"deal_breakers\": [\"string\"]
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# ---------------------------------------------------------------------------
# Evaluation prompts
# ---------------------------------------------------------------------------

# Purpose: compare résumé keywords against JD requirements; produce a score.
# Input to ask_json():
#   system=KEYWORD_MATCH_PROMPT
#   user="RÉSUMÉ PROFILE:\n{json}\n\nJD PROFILE:\n{json}"
# Expected output schema:
# {
#   "present": [{"keyword": "string", "category": "language|framework|tool|concept|soft_skill|buzzword",
#                "found_in": "summary|projects|experience|education|skills", "exact_match": true}],
#   "missing": [{"keyword": "string", "category": "...", "importance": "required|preferred",
#                "suggested_section": "skills|projects|experience|summary",
#                "why_it_matters": "string (25 words max — diagnostic only)"}],
#   "keyword_match_score": 0
# }
# Scoring formula: 100 × (required_skills found in résumé) / max(1, total required_skills)
# IMPORTANT: the résumé and JD profiles are always provided in full, even when
# they share zero keywords — that is a normal, valid input, not a missing one.
# The model must still return the schema (an empty "present" array is a
# correct result) rather than asking for clarification or claiming no résumé
# was given. Small/local models are especially prone to breaking character on
# a total-mismatch input, so state this constraint explicitly.
KEYWORD_MATCH_PROMPT = """
Instruction: Compare the résumé profile against the job-description profile and identify which required and preferred keywords are present or missing.

Context: The résumé and JD profiles are provided in full even when there are zero shared keywords. This is a normal valid input. You must still return the schema rather than asking for clarification or saying that no résumé was provided. The score should reflect the percentage of required skills found in the résumé.

Constraints: Use the provided profile data only. Do not invent keywords. Keep the output compact and structured. For each missing keyword, explain briefly why it matters in at most 25 words. Do not rewrite résumé content.

Output: Return a JSON object with this schema:
{
  \"present\": [{\"keyword\": \"string\", \"category\": \"language|framework|tool|concept|soft_skill|buzzword\", \"found_in\": \"summary|projects|experience|education|skills\", \"exact_match\": true}],
  \"missing\": [{\"keyword\": \"string\", \"category\": \"...\", \"importance\": \"required|preferred\", \"suggested_section\": \"skills|projects|experience|summary\", \"why_it_matters\": \"string (25 words max — diagnostic only)\"}],
  \"keyword_match_score\": 0
}

Scoring formula: 100 × (required_skills found in résumé) / max(1, total required_skills).

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# Purpose: score each résumé bullet against the Action → Technology → Impact rubric.
# Input to ask_json(): system=BULLET_QUALITY_PROMPT, user="RÉSUMÉ PROFILE:\n{json}"
# Expected output schema:
# {
#   "bullets": [{"source": "projects|experience", "parent_title": "string",
#                "bullet_text": "string (verbatim)", "has_action_verb": true,
#                "has_specific_technology": true, "has_measurable_impact": false,
#                "level": "L1_OK|L2_BETTER|L3_BEST",
#                "what_is_missing": "string (20 words max — diagnose only)"}],
#   "bullet_quality_avg": 0
# }
# Scoring formula: round(100 × sum(level_score) / (3 × count)) where L1=1, L2=2, L3=3
# IMPORTANT: embed the Action→Technology→Impact rubric verbatim inside this prompt,
# including the L1/L2/L3 reference level examples. This is a well-known, general
# résumé-writing framework — no external reference document needed.
BULLET_QUALITY_PROMPT = """
Instruction: Evaluate each résumé bullet against the Action → Technology → Impact rubric and score the overall bullet quality.

Context: The résumé profile contains bullets from projects and experience sections. The output should diagnose how well each bullet communicates impact. Use the rubric below verbatim.

Constraints: Evaluate only the bullet text that is provided. Do not invent missing details. Keep the diagnosis short and focused. Preserve the bullet text verbatim in the output. Do not rewrite résumé content.

Output: Return a JSON object with this schema:
{
  \"bullets\": [{\"source\": \"projects|experience\", \"parent_title\": \"string\", \"bullet_text\": \"string (verbatim)\", \"has_action_verb\": true, \"has_specific_technology\": true, \"has_measurable_impact\": false, \"level\": \"L1_OK|L2_BETTER|L3_BEST\", \"what_is_missing\": \"string (20 words max — diagnose only)\"}],
  \"bullet_quality_avg\": 0
}

ATI rubric:
- L1_OK: A bullet has an action verb and some context, but it lacks a specific technology or measurable impact.
- L2_BETTER: A bullet has an action verb, a specific technology, and some context, but the impact is still general or weakly quantified.
- L3_BEST: A bullet has a strong action verb, a specific technology, and clear measurable impact or outcome.

Scoring formula: round(100 × sum(level_score) / (3 × count)) where L1=1, L2=2, L3=3.

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# Purpose: detect résumé terminology that is a likely semantic match for JD
#          terminology but would not literally keyword-match an ATS scan.
# Input to ask_json():
#   system=JARGON_AUDIT_PROMPT
#   user="RÉSUMÉ PROFILE:\n{json}\n\nJD PROFILE:\n{json}"
# Expected output schema:
# {
#   "flags": [{"bullet_text": "string (verbatim)", "term_used": "string",
#              "suggested_translation": "string", "severity": "low|medium|high"}],
#   "jargon_score": 0
# }
# No static table: the model compares résumé text against JD text dynamically —
# a real ATS/recruiter tool does semantic matching, not a hand-maintained dictionary.
# Severity rules: high if the JD uses no equivalent language at all; medium if
# partial overlap; low if the JD already uses matching or adjacent terminology.
# Scoring formula: max(0, 100 - 10*high_count - 5*medium_count - 2*low_count)
JARGON_AUDIT_PROMPT = """
Instruction: Audit the résumé for terminology that may semantically match the job description even if it would not literally keyword-match an ATS scan.

Context: Compare the résumé text against the JD text dynamically. Do not rely on a fixed lookup table or hard-coded translation dictionary. This is a semantic match audit, not a literal string-match audit.

Constraints: Only use the provided résumé and JD data. Flag likely-equivalent wording that could help a recruiter or ATS understand the match. Severity rules: high if the JD uses no equivalent language at all; medium if there is partial overlap; low if the JD already uses matching or adjacent terminology. Do not rewrite résumé content.

Output: Return a JSON object with this schema:
{
  \"flags\": [{\"bullet_text\": \"string (verbatim)\", \"term_used\": \"string\", \"suggested_translation\": \"string\", \"severity\": \"low|medium|high\"}],
  \"jargon_score\": 0
}

Scoring formula: max(0, 100 - 10*high_count - 5*medium_count - 2*low_count).

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# Purpose: audit general ATS-parseability formatting.
# Input to ask_json(): system=STRUCTURE_AUDIT_PROMPT, user="RÉSUMÉ TEXT:\n\n{text}"
# Expected output schema:
# {
#   "page_count_estimate": 1,
#   "single_column_likely": true,
#   "section_headings_present": ["string"],
#   "section_headings_missing": ["string"],
#   "reverse_chronological_likely": true,
#   "contact_info_at_top": true,
#   "length_appropriate": true,
#   "no_images_or_graphics": true,
#   "ats_red_flags": [{"issue": "string", "evidence": "string"}],
#   "structure_score": 0
# }
# IMPORTANT: embed general ATS-parseability rules verbatim inside this prompt:
# single-column layout, standard section headers, reverse-chronological order,
# appropriate length, contact info placement, no images/graphics. These are
# well-known conventions — no external reference document needed.
STRUCTURE_AUDIT_PROMPT = """
Instruction: Audit the résumé for ATS-parseability and formatting quality.

Context: You are evaluating how likely the résumé is to be parsed and understood by applicant tracking systems and recruiters. Use the ATS-parseability rules below verbatim.

Constraints: Judge only from the provided résumé text. Do not assume missing information. Keep the output structured and concise. Do not rewrite résumé content.

Output: Return a JSON object with this schema:
{
  \"page_count_estimate\": 1,
  \"single_column_likely\": true,
  \"section_headings_present\": [\"string\"],
  \"section_headings_missing\": [\"string\"],
  \"reverse_chronological_likely\": true,
  \"contact_info_at_top\": true,
  \"length_appropriate\": true,
  \"no_images_or_graphics\": true,
  \"ats_red_flags\": [{\"issue\": \"string\", \"evidence\": \"string\"}],
  \"structure_score\": 0
}

ATS-parseability rules:
- Prefer a single-column layout with standard section headings such as Summary, Experience, Education, Skills, Projects.
- Use reverse-chronological order for experience and education when possible.
- Keep the résumé length appropriate for the candidate level and role.
- Place contact information near the top of the document.
- Avoid images, graphics, tables, or unusual formatting that may hinder parsing.

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# Purpose: assess how well the candidate's stated education/experience background
# plausibly aligns with what this role is asking for — using only data already
# extracted into resume_profile and jd_profile (no external degree code needed).
# Input to ask_json():
#   system=BACKGROUND_FIT_PROMPT
#   user="RÉSUMÉ PROFILE:\n{json}\n\nJD PROFILE:\n{json}"
# Expected output schema:
# {
#   "candidate_background_summary": "string (1–2 sentences)",
#   "role_requirements_summary": "string (1–2 sentences)",
#   "alignment_commentary": "string (2–3 sentences — diagnostic only)",
#   "background_fit_score": 0
# }
BACKGROUND_FIT_PROMPT = """
Instruction: Assess how well the candidate’s stated education and experience background plausibly aligns with the target role.

Context: Use only the résumé profile and job-description profile provided to you. Do not rely on outside knowledge, degree codes, or hidden context. The goal is a diagnostic assessment of fit based on the extracted data alone.

Constraints: Do not invent credentials or experience. Keep the response concise, structured, and evidence-based. Do not rewrite résumé content.

Output: Return a JSON object with this schema:
{
  \"candidate_background_summary\": \"string (1–2 sentences)\",
  \"role_requirements_summary\": \"string (1–2 sentences)\",
  \"alignment_commentary\": \"string (2–3 sentences — diagnostic only)\",
  \"background_fit_score\": 0
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# ---------------------------------------------------------------------------
# Synthesis prompt
# ---------------------------------------------------------------------------

# Purpose: produce a 3-bullet plain Markdown executive summary from the full report.
# Input to ask_text(): system=OVERALL_SUMMARY_PROMPT, user="ANALYSIS REPORT:\n{json}"
# Returns: plain Markdown string (not JSON).
# NOTE: this prompt does NOT need the JSON output constraint line.
#       It also does NOT need a JSON schema — ask_text() is used, not ask_json().
# The summary must be diagnostic only — no rewrites, no generated résumé content.
OVERALL_SUMMARY_PROMPT = """
Instruction: Produce a short diagnostic executive summary of the résumé analysis report.

Context: You will receive a JSON report containing the overall score, ATS threshold status, keyword match results, bullet quality, jargon audit, structure audit, and background-fit assessment. Summarise the most important findings in three concise bullet points.

Constraints: The summary must be diagnostic only. Do not rewrite the résumé, and do not generate new résumé content. Focus on strengths, gaps, and likely ATS or fit issues. Keep the output plain Markdown bullets without JSON formatting.

Output: Return exactly three bullet points in Markdown, with no surrounding prose or headings.
"""

DEGREE_ALIGNMENT_PROMPT = """\
You are a degree-alignment checker. You are given a JD profile JSON and the
student's degree program code. You check whether the JD job title is on the
suggested-titles list for the student's degree.

Degree-Aligned Job Title Lists
===============================
RTIS (Real-Time Interactive Simulation):
  Game Engine Developer, Systems Engineer, Site Reliability Engineer (SRE),
  DevOps Engineer, AI/ML Engineer, Data Analyst / Data Scientist,
  Full Stack Developer, Cybersecurity Engineer, Simulation Engineer,
  Graphics Programmer, Technical Product Manager, Technical Project Manager

IMGD (Interactive Media & Game Development):
  Game Developer, Systems Engineer, Full Stack Developer, Data Engineer,
  Infrastructure Engineer, DevOps Engineer, Cybersecurity Engineer,
  AI/ML Engineer, Technical Designer, Technical Artist,
  Gameplay Programmer, Tools Engineer,
  Technical Product Manager, Technical Project Manager

UXGD (User Experience & Game Design):
  App Developer, UI/UX Designer, Product Designer, Product Manager,
  Product Operations Manager, Project Manager, Marketing & Design Specialist,
  Process Architect, Technical Designer, Technical Artist,
  UX Researcher, UX Engineer

BFA (Digital Art and Animation):
  Technical Artist, UI/UX Designer, Creative Designer, Unreal Engine Artist,
  3D Graphic Artist, Production Assistant, Project Manager, Project Operations

Matching rule:
- title_on_suggested_list is true if the JD title matches an entry exactly OR
  is a clear variant (e.g. "Junior Systems Engineer" matches "Systems Engineer").
- If false, set degree_alignment_score to 50-70 with fit_commentary explaining
  the mismatch. Never invent a match.

JSON schema:

{
  "student_degree": "string",
  "jd_title": "string",
  "title_on_suggested_list": true,
  "matched_against": "string",
  "fit_commentary": "string (40 words or fewer)",
  "degree_alignment_score": 100
}

Output ONLY a valid JSON object matching the schema above. No prose. No
markdown fences. Never rewrite or generate résumé content.
"""