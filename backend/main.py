"""
main.py
-------
FastAPI backend for the RADIX JD Analytics Agent.

Endpoints:
  POST /api/analyze   -> upload a JD (.pdf/.docx), get structured RADIX JSON back
  GET  /api/health     -> health check
  POST /api/auth/signup -> user registration via Supabase
  POST /api/auth/signin -> user login via Supabase
  POST /api/analyses -> store analysis in Supabase
  GET  /api/analyses -> retrieve user analyses
"""

import os
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from extractor import extract_text, UnsupportedFileType
from llm_agent import analyze_job_description, AgentError
from supabase_client import init_supabase, get_supabase, store_analysis, get_user_analyses, upload_file_to_storage

app = FastAPI(title="RADIX JD Analytics Agent")

# Initialize Supabase
init_supabase()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Pydantic Models ----
class AuthRequest(BaseModel):
    email: str
    password: str

class AnalysisData(BaseModel):
    user_id: str
    file_name: str
    result: dict

MAX_FILE_SIZE_MB = 10


@app.get("/api/health")
def health():
    return {"status": "ok", "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-5")}


@app.post("/api/analyze")
async def analyze(file: Optional[UploadFile] = File(None), text: Optional[str] = Form(None)):
    jd_text = None

    if file is not None:
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
    elif text is not None:
        jd_text = text.strip()
    else:
        raise HTTPException(400, "Provide either a JD file or raw text input.")

    if not jd_text or len(jd_text.strip()) < 30:
        raise HTTPException(422, "No readable text found in the input.")

    try:
        result = analyze_job_description(jd_text)
    except AgentError as e:
        raise HTTPException(502, str(e))

    return result


# ---- Supabase Endpoints ----

@app.post("/api/analyses")
async def save_analysis(data: AnalysisData):
    """Store analysis result in Supabase"""
    try:
        result = store_analysis(data.user_id, data.file_name, data.result)
        if result:
            return {"success": True, "data": result}
        return {"success": False, "error": "Failed to store analysis"}
    except Exception as e:
        raise HTTPException(500, f"Error storing analysis: {str(e)}")


@app.get("/api/analyses/{user_id}")
async def get_analyses(user_id: str):
    """Retrieve analyses for a specific user"""
    try:
        analyses = get_user_analyses(user_id)
        return {"success": True, "data": analyses}
    except Exception as e:
        raise HTTPException(500, f"Error retrieving analyses: {str(e)}")


@app.post("/api/upload")
async def upload_to_storage(file: UploadFile = File(...), user_id: str = None):
    """Upload file to Supabase Storage"""
    try:
        if not user_id:
            raise HTTPException(400, "user_id is required")
        
        file_bytes = await file.read()
        url = upload_file_to_storage("job-descriptions", file.filename, file_bytes, user_id)
        
        if url:
            return {"success": True, "url": url}
        return {"success": False, "error": "Failed to upload file"}
    except Exception as e:
        raise HTTPException(500, f"Error uploading file: {str(e)}")


# ---- Serve the frontend (static single-page app) ----
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
