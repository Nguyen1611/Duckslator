"""
Job Routes for Duckslator

Simple job processing endpoints following the existing main.py pattern.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from datetime import datetime
from bson import ObjectId
import os
import shutil
import asyncio

from ..authentication.authentication import get_current_user
from ..database.connection import db

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def create_job(
    file: UploadFile = File(...), 
    target_lang: str = Form(...),
    current=Depends(get_current_user)
):
    """
    Create a new translation job.
    
    Uploads a file and creates a job record in the database.
    """
    now = datetime.utcnow()
    
    # Generate unique job ID
    job_id = ObjectId()
    
    # Create job-specific filename to avoid conflicts
    ext = os.path.splitext(file.filename)[-1]
    temp_filename = f"job_{str(job_id)}_input{ext}"
    file_path = os.path.join(UPLOAD_DIR, temp_filename)
    
    # Save uploaded file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create job record in database
    job = {
        "_id": job_id,
        "user_id": current["_id"],
        "original_filename": file.filename,
        "input_file_path": temp_filename,
        "target_lang": target_lang,
        "status": "queued",
        "progress": 0,
        "result_file_path": None,
        "created_at": now,
        "updated_at": now
    }
    
    await db.jobs.insert_one(job)
    
    return {
        "job_id": str(job_id),
        "status": "queued",
        "original_filename": file.filename,
        "target_lang": target_lang,
        "created_at": now
    }

@router.get("/")
async def list_user_jobs(current=Depends(get_current_user)):
    """
    Get all jobs for the current authenticated user.
    """
    cursor = db.jobs.find({"user_id": current["_id"]}).sort("created_at", -1)
    jobs = []
    
    async for job in cursor:
        job_data = {
            "job_id": str(job["_id"]),
            "original_filename": job.get("original_filename"),
            "target_lang": job.get("target_lang"),
            "status": job["status"],
            "progress": job.get("progress", 0),
            "created_at": job["created_at"],
            "updated_at": job.get("updated_at"),
            "files_available": not job.get("files_deleted", False)
        }
        
        # Add download URL for completed jobs
        if job["status"] == "completed" and not job.get("files_deleted", False):
            job_data["download_url"] = f"/jobs/{str(job['_id'])}/download"
            
        jobs.append(job_data)
    
    return {
        "jobs": jobs,
        "total": len(jobs)
    }

@router.get("/{job_id}")
async def get_job(job_id: str, current=Depends(get_current_user)):
    """
    Get specific job details.
    """
    job = await db.jobs.find_one({"_id": ObjectId(job_id), "user_id": current["_id"]})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = {
        "job_id": str(job["_id"]),
        "original_filename": job.get("original_filename"),
        "target_lang": job.get("target_lang"),
        "status": job["status"],
        "progress": job.get("progress", 0),
        "created_at": job["created_at"],
        "updated_at": job.get("updated_at"),
        "files_available": not job.get("files_deleted", False)
    }
    
    if job["status"] == "completed" and not job.get("files_deleted", False):
        job_data["download_url"] = f"/jobs/{str(job['_id'])}/download"
    
    return job_data

@router.delete("/{job_id}")
async def delete_job(job_id: str, current=Depends(get_current_user)):
    """
    Delete a specific job and its associated files.
    """
    job = await db.jobs.find_one({"_id": ObjectId(job_id), "user_id": current["_id"]})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete associated files from disk
    for file_field in ["input_file_path", "result_file_path"]:
        if job.get(file_field):
            file_path = os.path.join(UPLOAD_DIR, job[file_field])
            if os.path.exists(file_path):
                os.remove(file_path)
    
    # Remove job from database
    await db.jobs.delete_one({"_id": ObjectId(job_id)})
    
    return {"message": "Job and associated files deleted successfully"}

@router.post("/{job_id}/process")
async def process_job(job_id: str, current=Depends(get_current_user)):
    """
    Process a queued job (simulation).
    """
    job = await db.jobs.find_one({"_id": ObjectId(job_id), "user_id": current["_id"]})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "queued":
        raise HTTPException(status_code=400, detail="Job is not in queued status")
    
    input_file = job.get("input_file_path")
    if not input_file:
        raise HTTPException(status_code=400, detail="No input file found")
    
    # Construct file paths
    input_path = os.path.join(UPLOAD_DIR, input_file)
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="Input file missing")
    
    # Generate result filename
    ext = os.path.splitext(input_file)[1]
    result_filename = f"job_{job_id}_result{ext}"
    result_path = os.path.join(UPLOAD_DIR, result_filename)
    
    # Safely copy file in chunks
    try:
        with open(input_path, 'rb') as src:
            with open(result_path, 'wb') as dst:
                while True:
                    chunk = src.read(65536)
                    if not chunk:
                        break
                    dst.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
    # Update job status to completed
    await db.jobs.update_one(
        {"_id": ObjectId(job_id)},
        {
            "$set": {
                "status": "completed",
                "progress": 100,
                "result_file_path": result_filename,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {
        "message": "Job processing completed",
        "job_id": job_id,
        "status": "completed",
        "download_url": f"/jobs/{job_id}/download"
    }

@router.get("/{job_id}/download")
async def download_result(job_id: str, current=Depends(get_current_user)):
    """
    Download the result file for a completed job.
    """
    job = await db.jobs.find_one({"_id": ObjectId(job_id), "user_id": current["_id"]})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed")
    
    if not job.get("result_file_path"):
        raise HTTPException(status_code=404, detail="No result file available")
    
    # Construct full file path
    file_path = os.path.join(UPLOAD_DIR, job["result_file_path"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Result file missing from disk")
    
    # Generate user-friendly download filename
    original_name = os.path.splitext(job["original_filename"])[0]
    ext = os.path.splitext(job["result_file_path"])[1]
    download_filename = f"{original_name}_translated_{job['target_lang']}{ext}"
    
    return FileResponse(
        path=file_path, 
        filename=download_filename, 
        media_type="application/octet-stream"
    )

@router.get("/{job_id}/download/input")
async def download_input(job_id: str, current=Depends(get_current_user)):
    """
    Download the original input file for a job.
    """
    job = await db.jobs.find_one({"_id": ObjectId(job_id), "user_id": current["_id"]})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not job.get("input_file_path"):
        raise HTTPException(status_code=404, detail="Input file not available")
    
    # Construct full file path
    file_path = os.path.join(UPLOAD_DIR, job["input_file_path"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Input file missing from disk")
    
    return FileResponse(
        path=file_path, 
        filename=job["original_filename"], 
        media_type="application/octet-stream"
    )

@router.get("/latest/completed")
async def get_latest_completed_job(current=Depends(get_current_user)):
    """
    Get the most recent completed job for the current user.
    """
    job = await db.jobs.find_one(
        {"user_id": current["_id"], "status": "completed"},
        sort=[("created_at", -1)]
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="No completed jobs found")
    
    job_data = {
        "job_id": str(job["_id"]),
        "original_filename": job.get("original_filename"),
        "target_lang": job.get("target_lang"),
        "status": job["status"],
        "progress": job.get("progress", 0),
        "created_at": job["created_at"],
        "updated_at": job.get("updated_at"),
        "download_url": f"/jobs/{str(job['_id'])}/download"
    }
    
    return job_data
