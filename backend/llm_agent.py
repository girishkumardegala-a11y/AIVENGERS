"""
llm_agent.py
------------
Core "RADIX" Job Description Analytics Agent.
Sends extracted JD text to Claude with a strict system prompt and
returns validated, deduplicated, schema-conformant JSON.
"""

import json
import os
import re

import anthropic

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

VALID_CATEGORY_CODES = {
    "COD", "DSA", "OOD", "APTI", "COMM", "AI",
    "CLOUD", "SQL", "SWE", "SYSD", "NETW", "OS",
}

SYSTEM_PROMPT = """You are an expert AI Job Description Analytics Agent for the RADIX Talent Match platform.

Your job: read the Job Description text you are given and convert it into clean, structured JSON.
Only use information explicitly mentioned or strongly implied in the text. Never invent details.

Extract:
- Company name
- Job role/position, department, employment type, location, experience required, education requirements
- All technical skills (languages, frameworks, tools, databases, cloud, AI/ML, system design, etc.)
- All soft skills (communication, teamwork, leadership, problem-solving, etc.)

Categorize every single extracted skill into EXACTLY ONE of these RADIX categories:

COD  - Coding: programming languages, frameworks, scripting/frontend/backend tech (e.g. Python, Java, React, Node.js, Django)
DSA  - Data Structures & Algorithms (e.g. Arrays, Trees, Graphs, Dynamic Programming, Hashing)
OOD  - Object-Oriented Design (e.g. OOP, SOLID Principles, Design Patterns, UML)
APTI - Aptitude: logical/quantitative reasoning (e.g. Analytical Skills, Quantitative Aptitude)
COMM - Communication & interpersonal skills (e.g. Communication, Teamwork, Leadership, Presentation)
AI   - Artificial Intelligence / ML (e.g. Machine Learning, NLP, TensorFlow, PyTorch, LangChain, RAG)
CLOUD- Cloud & DevOps platforms (e.g. AWS, Azure, GCP, Kubernetes, Docker, Terraform)
SQL  - Databases & data storage (e.g. SQL, PostgreSQL, MySQL, MongoDB, Redis)
SWE  - Software engineering practices (e.g. Git, REST APIs, CI/CD, Agile, Scrum, Testing, Microservices)
SYSD - Large-scale system architecture (e.g. System Design, Scalability, Load Balancing, Distributed Systems)
NETW - Networking (e.g. TCP/IP, DNS, HTTP/HTTPS, Routing, Firewalls)
OS   - Operating Systems (e.g. Linux, Windows, Processes, Threads, Memory Management)

Assign a confidence to every skill:
- "High"   -> explicitly mentioned in the JD text
- "Medium" -> strongly implied
- "Low"    -> weak inference
Never assign "High" unless the skill is directly mentioned in the text.

Validation rules:
- Output ONLY valid JSON. No markdown, no code fences, no commentary, no explanations.
- No duplicate skills. Normalize obvious duplicates (e.g. "JS" -> "JavaScript", "Py" -> "Python") but preserve the standard/common name.
- Each skill belongs to exactly one category.
- If a field is missing from the JD, use "" (string fields) or [] (array fields). Never invent data.

Return JSON matching EXACTLY this schema and nothing else:

{
  "source_type": "jd",
  "company": "",
  "role": "",
  "department": "",
  "employment_type": "",
  "location": "",
  "experience": "",
  "education": "",
  "technologies": [],
  "skills": [
    {"skill_name": "", "category_code": "", "confidence": ""}
  ]
}
"""


class AgentError(Exception):
    pass


def analyze_job_description(jd_text: str) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise AgentError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file (see .env.example)."
        )

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this Job Description and return the JSON:\n\n{jd_text}",
                }
            ],
        )
    except anthropic.APIError as e:
        raise AgentError(f"Claude API error: {e}")

    raw_text = "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    )

    data = _parse_json(raw_text)
    data = _validate_and_clean(data)
    return data


def _parse_json(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned.strip())
    cleaned = re.sub(r"```$", "", cleaned.strip())
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fall back to extracting the first {...} block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise AgentError("Model did not return valid JSON.")


def _validate_and_clean(data: dict) -> dict:
    schema_defaults = {
        "source_type": "jd",
        "company": "",
        "role": "",
        "department": "",
        "employment_type": "",
        "location": "",
        "experience": "",
        "education": "",
        "technologies": [],
        "skills": [],
    }

    for key, default in schema_defaults.items():
        data.setdefault(key, default)

    data["source_type"] = "jd"

    # Dedupe skills (case-insensitive on skill_name) and drop invalid categories
    seen = set()
    clean_skills = []
    for skill in data.get("skills", []):
        name = str(skill.get("skill_name", "")).strip()
        code = str(skill.get("category_code", "")).strip().upper()
        confidence = str(skill.get("confidence", "")).strip().capitalize()

        if not name or code not in VALID_CATEGORY_CODES:
            continue
        if confidence not in {"High", "Medium", "Low"}:
            confidence = "Low"

        key = name.lower()
        if key in seen:
            continue
        seen.add(key)

        clean_skills.append({
            "skill_name": name,
            "category_code": code,
            "confidence": confidence,
        })

    data["skills"] = clean_skills

    # Dedupe technologies list, preserve order
    seen_tech = set()
    clean_tech = []
    for tech in data.get("technologies", []):
        t = str(tech).strip()
        if t and t.lower() not in seen_tech:
            seen_tech.add(t.lower())
            clean_tech.append(t)
    data["technologies"] = clean_tech

    return data
