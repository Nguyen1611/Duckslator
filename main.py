from datetime import datetime

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, status, Form
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo import ReturnDocument

from auth import create_access_token, decode_token, hash_pw, verify_pw
from db import users_coll, db
from models import Token, UserCreate, UserOut

from fastapi import File, UploadFile
from fastapi.responses import FileResponse
import os
import shutil
import uuid

import asyncio

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.on_event("startup")
async def init_indexes() -> None:
    await users_coll.create_index("email", unique=True)
    await db.jobs.create_index("user_id")

@app.post("/register", response_model=UserOut)
async def register(payload: UserCreate):
    if await users_coll.find_one({"email": payload.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    now = datetime.utcnow()
    doc = {
        "name": {"first": payload.first_name, "last": payload.last_name},
        "age": payload.age,
        "email": payload.email,
        "passwordHash": hash_pw(payload.password),
        "membership": {"tier": "normal", "since": now},
        "usage": {
            "videosTranslated": 0,
            "minutesTranslated": 0,
            "lastReset": now,
        },
        "createdAt": now,
        "updatedAt": now,
    }

    result = await users_coll.insert_one(doc)
    return UserOut(
        id=str(result.inserted_id),
        firstName=doc["name"]["first"],
        lastName=doc["name"]["last"],
        email=doc["email"],
    )

@app.post("/login", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user = await users_coll.find_one({"email": form.username})
    if not user or not verify_pw(form.password, user["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token({"sub": str(user["_id"]), "email": user["email"]})
    return Token(access_token=token)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        uid = payload.get("sub")
        if uid is None:
            raise ValueError
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = await users_coll.find_one({"_id": ObjectId(uid)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/me", response_model=UserOut)
async def me(current=Depends(get_current_user)):
    return UserOut(
        id=str(current["_id"]),
        firstName=current["name"]["first"],
        lastName=current["name"]["last"],
        email=current["email"],
    )

@app.post("/jobs")
async def create_job(
    file: UploadFile = File(...), 
    target_lang: str = Form(...),
    current=Depends(get_current_user)
):
    now = datetime.utcnow()
    
    # Generate job ID first
    job_id = ObjectId()
    
    # Save uploaded file temporarily with job-specific name
    ext = os.path.splitext(file.filename)[-1]
    temp_filename = f"job_{str(job_id)}_input{ext}"
    file_path = os.path.join(UPLOAD_DIR, temp_filename)
    
    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create job record (no videos collection)
    job = {
        "_id": job_id,
        "user_id": current["_id"],
        "original_filename": file.filename,
        "input_file_path": temp_filename,  # Store relative path for input
        "target_lang": target_lang,
        "status": "queued",
        "progress": 0,
        "result_file_path": None,  # Will be set when processing completes
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

@app.get("/jobs")
async def list_user_jobs(current=Depends(get_current_user)):
    """Get all jobs for the current user"""
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
        
        # Only include download URL if job is completed and files still exist
        if job["status"] == "completed" and not job.get("files_deleted", False):
            job_data["download_url"] = f"/jobs/{str(job['_id'])}/download"
            
        jobs.append(job_data)
    
    return {
        "jobs": jobs,
        "total": len(jobs)
    }

async def cleanup_job_files(job_id: str):
    """Clean up video files after download, but keep job metadata"""
    try:
        # Small delay to ensure download completes
        await asyncio.sleep(2)
        
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            return
        
        # Delete input and result files from disk
        files_to_delete = []
        if job.get("input_file_path"):
            files_to_delete.append(job["input_file_path"])
        if job.get("result_file_path"):
            files_to_delete.append(job["result_file_path"])
        
        for file_path in files_to_delete:
            full_path = os.path.join(UPLOAD_DIR, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                print(f"Deleted file: {full_path}")
        
        # Update job record to mark files as deleted
        await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "files_deleted": True,
                    "files_deleted_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$unset": {
                    "input_file_path": "",
                    "result_file_path": ""
                }
            }
        )
        print(f"Cleaned up files for job {job_id}")
        
    except Exception as e:
        print(f"Error cleaning up files for job {job_id}: {e}")

@app.get("/download/latest")
async def download_latest_result(current=Depends(get_current_user)):
    """Download the most recent completed job result"""
    
    # Find the most recent completed job for this user
    job = await db.jobs.find_one(
        {"user_id": current["_id"], "status": "completed"},
        sort=[("created_at", -1)]
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="No completed jobs found")
    
    if not job.get("result_file_path"):
        raise HTTPException(status_code=404, detail="No result file available")
    
    file_path = os.path.join(UPLOAD_DIR, job["result_file_path"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Result file missing from disk")
    
    # Generate a nice filename for download
    original_name = os.path.splitext(job["original_filename"])[0]
    ext = os.path.splitext(job["result_file_path"])[1]
    download_filename = f"{original_name}_translated_{job['target_lang']}{ext}"
    
    # Create the file response
    response = FileResponse(
        path=file_path, 
        filename=download_filename, 
        media_type="application/octet-stream"
    )
    
    asyncio.create_task(cleanup_job_files(str(job["_id"])))
    
    return response

@app.post("/simulate-latest-job")
async def simulate_latest_job_processing(current=Depends(get_current_user)):
    """Simulate processing completion for the most recent queued job"""
    
    # Find the most recent queued job
    job = await db.jobs.find_one(
        {"user_id": current["_id"], "status": "queued"},
        sort=[("created_at", -1)]
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="No queued jobs found")
    
    job_id = str(job["_id"])
    
    # Use the existing simulate function logic
    input_file = job.get("input_file_path")
    if not input_file:
        raise HTTPException(status_code=400, detail="No input file found")
    
    input_path = os.path.join(UPLOAD_DIR, input_file)
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="Input file missing")
    
    # Generate result filename
    ext = os.path.splitext(input_file)[1]
    result_filename = f"job_{job_id}_result{ext}"
    result_path = os.path.join(UPLOAD_DIR, result_filename)
    
    # Copy input file to result file (simulating processing) - SAFE METHOD
    try:
        with open(input_path, 'rb') as src:
            with open(result_path, 'wb') as dst:
                while True:
                    chunk = src.read(65536)  # 64KB chunks
                    if not chunk:
                        break
                    dst.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copy failed: {str(e)}")

    # Verify copy was successful
    if os.path.getsize(input_path) != os.path.getsize(result_path):
        raise HTTPException(status_code=500, detail="File copy verification failed")
    # Update job status
    await db.jobs.update_one(
        {"_id": job["_id"]},
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
        "message": "Latest job processing simulated successfully",
        "job_id": job_id,
        "status": "completed",
        "download_url": "/download/latest"
    }

@app.post("/simulate-latest-job-safe-copy")
async def simulate_latest_job_safe_copy(current=Depends(get_current_user)):
    """Simulate processing with safer file copy method"""
    
    # Find the most recent queued job
    job = await db.jobs.find_one(
        {"user_id": current["_id"], "status": "queued"},
        sort=[("created_at", -1)]
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="No queued jobs found")
    
    job_id = str(job["_id"])
    input_file = job.get("input_file_path")
    
    if not input_file:
        raise HTTPException(status_code=400, detail="No input file found")
    
    input_path = os.path.join(UPLOAD_DIR, input_file)
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="Input file missing")
    
    # Generate result filename
    ext = os.path.splitext(input_file)[1]
    result_filename = f"job_{job_id}_result{ext}"
    result_path = os.path.join(UPLOAD_DIR, result_filename)
    
    # Use binary copy instead of shutil.copy2
    try:
        with open(input_path, 'rb') as src:
            with open(result_path, 'wb') as dst:
                # Copy in chunks to avoid memory issues
                while True:
                    chunk = src.read(65536)  # 64KB chunks
                    if not chunk:
                        break
                    dst.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copy failed: {str(e)}")
    
    # Verify file sizes match
    original_size = os.path.getsize(input_path)
    copied_size = os.path.getsize(result_path)
    
    if original_size != copied_size:
        raise HTTPException(status_code=500, detail=f"Copy verification failed: {original_size} != {copied_size}")
    
    # Update job status
    await db.jobs.update_one(
        {"_id": job["_id"]},
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
        "message": "Job processing simulated with safe copy",
        "job_id": job_id,
        "status": "completed",
        "original_size": original_size,
        "copied_size": copied_size,
        "download_url": "/download/latest"
    }

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str, current=Depends(get_current_user)):
    job = await db.jobs.find_one({"_id": ObjectId(job_id), "user_id": current["_id"]})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete files from disk
    for file_field in ["input_file_path", "result_file_path"]:
        if job.get(file_field):
            file_path = os.path.join(UPLOAD_DIR, job[file_field])
            if os.path.exists(file_path):
                os.remove(file_path)
    
    # Delete job from database
    await db.jobs.delete_one({"_id": ObjectId(job_id)})
    
    return {"message": "Job and associated files deleted successfully"}

@app.get("/download/original/{job_id}")
async def download_original_file(job_id: str, current=Depends(get_current_user)):
    """Download the original uploaded file to test if it's playable"""
    
    job = await db.jobs.find_one({"_id": ObjectId(job_id), "user_id": current["_id"]})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not job.get("input_file_path"):
        raise HTTPException(status_code=404, detail="No input file available")
    
    file_path = os.path.join(UPLOAD_DIR, job["input_file_path"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Input file missing from disk")
    
    return FileResponse(
        path=file_path, 
        filename=f"original_{job['original_filename']}", 
        media_type="application/octet-stream"
    )