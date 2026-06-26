import json
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

BASE_DIR = Path(__file__).parent.resolve()

# Load environment variables from the project root so the app sees .env reliably
load_dotenv(BASE_DIR / ".env", override=True)

from services import zip_handler, skill_detector, gemini_service

app = FastAPI(title="Project Evaluator")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job state store
jobs = {}

# Background processing helper
async def process_submission(job_id: str, project_name: str, description: str, zip_path: str):
    jobs[job_id]["status"] = "extracting"
    tmp_base = zip_handler.get_tmp_base()
    extracted_path = tmp_base / "extracted" / job_id
    
    try:
        # Step 1: Extract and get tree
        _ = zip_handler.extract_zip(zip_path, job_id)
        file_info = zip_handler.get_file_tree(str(extracted_path))
        
        # Step 2: Detect skills
        jobs[job_id]["status"] = "detecting"
        skill_info = skill_detector.detect_skills(
            file_info["extensions"],
            file_info["source_code"]
        )
        
        # Step 3: Call Gemini API
        jobs[job_id]["status"] = "analyzing"
        gemini_result = await gemini_service.analyze_project(
            description,
            file_info,
            skill_info,
            project_name=project_name,
        )
        
        # Check for errors returned in Gemini results
        if "error" in gemini_result and gemini_result["error"] == "AI analysis failed":
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = gemini_result.get("detail", "Gemini API request failed")
            jobs[job_id]["result"] = {
                "project_name": project_name,
                "skills": skill_info,
                "file_count": file_info["total_files"],
                "gemini": gemini_result
            }
            return

        # Step 4: Done
        jobs[job_id]["status"] = "done"
        jobs[job_id]["result"] = {
            "project_name": project_name,
            "skills": skill_info,
            "file_count": file_info["total_files"],
            "gemini": gemini_result
        }
        
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        
    finally:
        # Resource cleanups
        zip_handler.cleanup(str(extracted_path))
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception:
            pass


# --- API Endpoints ---

@app.get("/")
async def serve_index():
    """
    Serve index.html at GET / as a static file.
    """
    index_file = BASE_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_file)


@app.post("/submit")
async def submit_project(
    project_name: str = Form(...),
    description: str = Form(""),
    zip_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Submit project ZIP and metadata.
    Saves ZIP and triggers background processing task.
    """
    filename = zip_file.filename or ""
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are accepted")
        
    job_id = str(uuid.uuid4())[:8]
    
    # Save upload to a temp ZIP path
    tmp_base = zip_handler.get_tmp_base()
    zip_path = tmp_base / f"{job_id}.zip"
    
    try:
        content = await zip_file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="ZIP file is empty")
        with open(zip_path, "wb") as f:
            f.write(content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload ZIP: {str(e)}")
        
    # Store initial status
    jobs[job_id] = {
        "status": "extracting",
        "error": None,
        "result": None
    }
    
    background_tasks.add_task(
        process_submission,
        job_id,
        project_name,
        description,
        str(zip_path)
    )
    
    return {"job_id": job_id}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    Get job status.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = jobs[job_id]
    response = {"status": job["status"]}
    if job["error"]:
        response["error"] = job["error"]
        
    return response


@app.get("/result/{job_id}")
async def get_result(job_id: str):
    """
    Get full evaluation result once complete.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = jobs[job_id]
    if job["status"] == "error" and job["result"]:
        return job["result"]
    elif job["status"] != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not done. Current status: {job['status']}"
        )
        
    return job["result"]


@app.post("/save-report")
async def save_report(payload: dict):
    """
    Persist the submitted evaluation payload as a JSON file inside the project folder.
    """
    try:
        project_name = (payload.get("project_name") or "project").strip() or "project"
        safe_name = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in project_name).strip()
        safe_name = safe_name.replace(" ", "_").lower() or "project"
        file_name = f"{safe_name}_evaluation.json"
        save_path = BASE_DIR / file_name

        with open(save_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.write("\n")

        return JSONResponse({"status": "saved", "saved_path": file_name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save report: {str(e)}")
