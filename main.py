from datetime import datetime

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, status, Form, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo import ReturnDocument

from dotenv import load_dotenv

from pipeline.authentication.auth import create_access_token, decode_token, hash_pw, verify_pw
from pipeline.database.connection import users_coll, db
from pipeline.database.models import Token, UserCreate, UserOut

from fastapi import File, UploadFile
from fastapi.responses import FileResponse
import os
import shutil
import uuid

import asyncio
from fastapi.middleware.cors import CORSMiddleware

from pipeline.authentication.google_auth import verify_google_token
from pipeline.database.models import GoogleAuthRequest, GoogleUserInfo

from fastapi.responses import JSONResponse
from typing import Optional

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets

load_dotenv()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

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
    
    verification_token = generate_verification_token()
    now = datetime.utcnow()
    doc = {
        "name": {"first": payload.first_name, "last": payload.last_name},
        "age": payload.age,
        "email": payload.email,
        "passwordHash": hash_pw(payload.password),
        "email_verified": False,
        "verification_token": verification_token,
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
    
    # Send verification email
    await send_verification_email(payload.email, verification_token)
    
    return UserOut(
        id=str(result.inserted_id),
        firstName=doc["name"]["first"],
        lastName=doc["name"]["last"],
        email=doc["email"],
        email_verified=False
    )

def generate_verification_token():
    return secrets.token_urlsafe(32)

async def send_verification_email(email: str, token: str):
    """Send verification email - fixed version"""
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    
    if not sender_email or not sender_password:
        print("SMTP credentials not configured, skipping email send")
        return False
    
    verification_url = f"http://127.0.0.1:8000/verify-email/{token}"
    body = f"""
    Welcome to Duckslator!
    
    Please verify your email by clicking this link:
    {verification_url}
    
    If you didn't create this account, please ignore this email.
    """
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = "Verify your Duckslator account"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"Verification email sent to {email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {email}: {e}")
        return False

async def get_current_user(request: Request, token: Optional[str] = Depends(oauth2_scheme)):
    try:
        if not token:
            token = request.cookies.get("access_token")
        if not token:
            raise ValueError
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

# Add Google OAuth endpoints
@app.post("/auth/google", response_model=Token)
async def google_auth(request: GoogleAuthRequest, response: Response):
    """Authenticate user with Google OAuth"""
    try:
        # Verify Google token
        google_user = await verify_google_token(request.id_token)
        
        # Check if email is verified
        if not google_user['email_verified']:
            raise HTTPException(
                status_code=400, 
                detail="Email not verified with Google"
            )
        
        # Check if user exists
        existing_user = await users_coll.find_one({"email": google_user['email']})
        
        if existing_user:
            token = create_access_token({
                "sub": str(existing_user["_id"]),
                "email": existing_user["email"]
            })
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                samesite="lax",
                secure=False,  # set True in production (HTTPS)
                max_age=60 * 60,
            )
            return Token(access_token=token)
        else:
            # Create new user from Google info
            now = datetime.utcnow()
            names = google_user['name'].split(' ', 1)
            first_name = names[0] if names else "Unknown"
            last_name = names[1] if len(names) > 1 else ""
            
            doc = {
                "google_id": google_user['sub'],
                "name": {"first": first_name, "last": last_name},
                "email": google_user['email'],
                "email_verified": True,
                "picture": google_user.get('picture'),
                "auth_provider": "google",
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
            
            token = create_access_token({
                "sub": str(result.inserted_id), 
                "email": doc["email"]
            })
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                samesite="lax",
                secure=False,  # set True in production (HTTPS)
                max_age=60 * 60,
            )
            return Token(access_token=token)
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Authentication failed")

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

@app.post("/login", response_model=Token)
async def login(response: Response, form: OAuth2PasswordRequestForm = Depends()):
    user = await users_coll.find_one({"email": form.username})
    if not user or not verify_pw(form.password, user["passwordHash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    
    if not user.get("email_verified", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please verify your email before logging in")
    
    token = create_access_token({"sub": str(user["_id"]), "email": user["email"]})
    response.set_cookie("access_token", token, httponly=True, samesite="lax", secure=False, max_age=60*60)
    return Token(access_token=token)

@app.post("/logout")
def logout():
    resp = JSONResponse({"message": "logged out"})
    resp.delete_cookie("access_token")
    return resp

