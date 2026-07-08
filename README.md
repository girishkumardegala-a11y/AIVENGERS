# RADIX — JD Analytics Agent

An AI agent that reads a Job Description (PDF or DOCX) and converts it into
structured JSON: company/role details, extracted skills, and each skill mapped
to one of 12 RADIX taxonomy categories with a confidence score.

Built for a hackathon: FastAPI backend + a dependency-free HTML/CSS/JS frontend,
powered by the Claude API for extraction and categorization.

```
jd-agent/
├── backend/
│   ├── main.py          FastAPI app (routes + serves the frontend)
│   ├── extractor.py      PDF/DOCX -> clean text
│   ├── llm_agent.py       Claude prompt, JSON parsing, validation/cleanup
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

## 1. Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and paste your ANTHROPIC_API_KEY
```

Get a key at https://console.anthropic.com/settings/keys if you don't have one.

## 2. Run

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000** — the frontend is served directly by the backend,
so there's nothing else to start.

## 3. Use it

1. Drop a `.pdf` or `.docx` Job Description into the intake panel.
2. Click **Scan document**.
3. The agent extracts text, sends it to Claude with a strict RADIX-taxonomy
   prompt, and returns validated JSON: job details, a 12-category signal grid,
   and the full skill list grouped by category with confidence badges.
4. Click **Download JSON** to grab the raw output for downstream modules
   (e.g. a Skill Matching service).

## API

`POST /api/analyze` — multipart form upload, field name `file` (`.pdf`/`.docx`, ≤10MB).

Response:
```json
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
    { "skill_name": "", "category_code": "", "confidence": "" }
  ]
}
```

`category_code` is one of: `COD, DSA, OOD, APTI, COMM, AI, CLOUD, SQL, SWE, SYSD, NETW, OS`.
`confidence` is one of: `High, Medium, Low`.

`GET /api/health` — quick check that the server + configured model are up.

## Design notes / what makes this "fully functional"

- **Real text extraction**, not just filename sniffing: `pdfplumber` for PDFs
  (with automatic header/footer/page-number stripping across pages) and
  `python-docx` for Word docs (paragraphs + tables).
- **Strict, schema-locked prompting**: the system prompt embeds the full RADIX
  mapping table and confidence rules from the spec, and instructs Claude to
  return JSON only.
- **Server-side validation layer** (`_validate_and_clean` in `llm_agent.py`)
  is a safety net independent of the model's own discipline: it strips
  markdown code fences if the model adds them anyway, drops any skill with an
  invalid category code, de-duplicates skills case-insensitively, normalizes
  confidence values, and guarantees every schema field is present — so the
  API contract holds even if the model's output isn't perfect.
- **Sensible errors**: unsupported file types, oversized files, unreadable/empty
  documents, and missing API keys all return clear HTTP errors instead of
  crashing.

## Extending it for the rest of your pipeline

- Swap `analyze_job_description` in `llm_agent.py` for a different model/provider
  without touching `main.py` or the frontend — it's fully isolated behind the
  same function signature.
- The output JSON is exactly what a "Skill Matching" module would consume next —
  pair a similarly-shaped resume/CV analyzer against the same RADIX taxonomy and
  diff `skills[]` arrays for a match score.
