"""
main.py
-------
FastAPI backend for the RADIX JD Analytics Agent.

Endpoints:
  POST /api/analyze   -> upload a JD (.pdf/.docx), get structured RADIX JSON back
  GET  /api/health     -> health check
"""

import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from extractor import extract_text, UnsupportedFileType
from llm_agent import analyze_job_description, AgentError

app = FastAPI(title="RADIX JD Analytics Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE_MB = 10


@app.get("/api/health")
def health():
    return {"status": "ok", "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-5")}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(400, "Only .pdf and .docx files are supported.")

    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(400, f"File too large ({size_mb:.1f} MB). Max {MAX_FILE_SIZE_MB} MB.")

    try:
        jd_text = extract_text(file.filename, file_bytes)
    except UnsupportedFileType as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(422, f"Could not extract text from file: {e}")

    if not jd_text or len(jd_text.strip()) < 30:
        raise HTTPException(422, "No readable text found in the document.")

    try:
        result = analyze_job_description(jd_text)
    except AgentError as e:
        raise HTTPException(502, str(e))

    return result


# ---- Serve the frontend (static single-page app) ----
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
