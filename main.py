from datetime import datetime, timedelta

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

from fastapi.responses import HTMLResponse

import re

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
    # Check if email already exists
    if await users_coll.find_one({"email": payload.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password strength
    password_validation = validate_password_strength(payload.password)
    if not password_validation["valid"]:
        raise HTTPException(status_code=400, detail=password_validation["message"])
    
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

def validate_password_strength(password: str) -> dict:
    """Validate password meets all requirements"""
    if len(password) < 8:
        return {
            "valid": False,
            "message": "Password must be at least 8 characters long"
        }
    
    if not re.search(r'[A-Z]', password):
        return {
            "valid": False,
            "message": "Password must contain at least one uppercase letter"
        }
    
    if not re.search(r'[a-z]', password):
        return {
            "valid": False,
            "message": "Password must contain at least one lowercase letter"
        }
    
    if not re.search(r'[0-9]', password):
        return {
            "valid": False,
            "message": "Password must contain at least one number"
        }
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return {
            "valid": False,
            "message": "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
        }
    
    return {"valid": True, "message": "Password meets all requirements"}

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

@app.post("/resend-verification-email")
async def resend_verification_email(email: str):
    """Resend verification email for unverified accounts"""
    user = await users_coll.find_one({"email": email})
    if not user:
        return {"message": "If the email exists, a verification email has been sent"}
    
    if user.get("email_verified", False):
        return {"message": "Email is already verified"}
    
    # Generate new verification token
    verification_token = generate_verification_token()
    
    # Update user with new token
    await users_coll.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "verification_token": verification_token,
                "updatedAt": datetime.utcnow()
            }
        }
    )
    
    # Send verification email
    await send_verification_email(email, verification_token)
    return {"message": f"Verification email sent to {email}"}

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

def generate_password_reset_token():
    return secrets.token_urlsafe(32)

@app.post("/forgot-password")
async def forgot_password(email: str):
    """Request password reset for email/password users"""
    user = await users_coll.find_one({"email": email})
    if not user:
        # Don't reveal if user exists or not (security best practice)
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Only allow password reset for email/password users, not Google users
    if user.get("auth_provider") == "google":
        return {"message": "Google users cannot reset password through this method"}
    
    # Generate reset token
    reset_token = generate_password_reset_token()
    token_expiry = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
    
    # Store reset token and expiry
    await users_coll.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_reset_token": reset_token,
                "password_reset_expiry": token_expiry,
                "updatedAt": datetime.utcnow()
            }
        }
    )
    
    # Send password reset email
    reset_url = f"http://127.0.0.1:8000/reset-password?token={reset_token}"
    body = f"""
    Password Reset Request
    
    You requested a password reset for your Duckslator account.
    
    Click this link to reset your password:
    {reset_url}
    
    This link expires in 24 hours.
    
    If you didn't request this, please ignore this email.
    """
    
    # Send email using your existing email function
    email_sent = await send_password_reset_email(email, body)
    
    if email_sent:
        return {"message": "Password reset email sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send password reset email")

async def send_password_reset_email(email: str, body: str):
    """Send password reset email"""
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    
    if not sender_email or not sender_password:
        print("SMTP credentials not configured, skipping email send")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = "Password Reset - Duckslator"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"Password reset email sent to {email}")
        return True
    except Exception as e:
        print(f"Failed to send password reset email to {email}: {e}")
        return False



"""
These 2 functions below are important for the password reset process.
The get endpoint shows the password reset form.
The post endpoint processes the password reset.
User never manually use these 2 endpoints but we have to keep it because browser needs it.
Can hide it when design UI later.
"""

@app.get("/reset-password")
async def reset_password_page(token: str):
    """Show password reset form page with real-time visual validation"""
    user = await users_coll.find_one({
        "password_reset_token": token,
        "password_reset_expiry": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        return {"error": "Invalid or expired reset token"}
    
    # Enhanced form with real-time visual validation
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reset Password</title>
        <style>
            .requirement {{
                margin: 5px 0;
                padding: 5px;
                border-radius: 3px;
                transition: all 0.3s ease;
            }}
            .requirement.met {{
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            .requirement.not-met {{
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            .check-icon {{
                margin-right: 8px;
                font-weight: bold;
            }}
            .password-field {{
                margin: 10px 0;
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                width: 250px;
                font-size: 14px;
            }}
            .password-field:focus {{
                border-color: #007bff;
                outline: none;
                box-shadow: 0 0 5px rgba(0,123,255,0.3);
            }}
            .reset-button {{
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 10px;
            }}
            .reset-button:hover {{
                background-color: #0056b3;
            }}
            .reset-button:disabled {{
                background-color: #6c757d;
                cursor: not-allowed;
            }}
            .container {{
                max-width: 500px;
                margin: 50px auto;
                padding: 20px;
                font-family: Arial, sans-serif;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Reset Your Password</h2>
            
            <div style="margin-bottom: 20px;">
                <h3>Password Requirements:</h3>
                <div class="requirement not-met" id="length-check">
                    <span class="check-icon">❌</span>At least 8 characters long
                </div>
                <div class="requirement not-met" id="uppercase-check">
                    <span class="check-icon">❌</span>At least one uppercase letter (A-Z)
                </div>
                <div class="requirement not-met" id="lowercase-check">
                    <span class="check-icon">❌</span>At least one lowercase letter (a-z)
                </div>
                <div class="requirement not-met" id="number-check">
                    <span class="check-icon">❌</span>At least one number (0-9)
                </div>
                <div class="requirement not-met" id="special-check">
                    <span class="check-icon">❌</span>At least one special character (!@#$%^&*(),.?":{{}}|<>)</span>
                </div>
                <div class="requirement not-met" id="match-check">
                    <span class="check-icon">❌</span>Passwords match
                </div>
            </div>
            
            <input type="password" id="new_password" class="password-field" placeholder="New Password" required><br>
            <input type="password" id="confirm_password" class="password-field" placeholder="Confirm New Password" required><br>
            <button id="reset-btn" class="reset-button" onclick="resetPassword()" disabled>Reset Password</button>
        </div>
        
        <script>
        function updateValidation() {{
            const newPassword = document.getElementById('new_password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            const resetBtn = document.getElementById('reset-btn');
            
            // Check each requirement
            const lengthMet = newPassword.length >= 8;
            const uppercaseMet = /[A-Z]/.test(newPassword);
            const lowercaseMet = /[a-z]/.test(newPassword);
            const numberMet = /[0-9]/.test(newPassword);
            const specialMet = /[!@#$%^&*(),.?":{{}}|<>]/.test(newPassword);
            const matchMet = newPassword === confirmPassword && newPassword.length > 0;
            
            // Update visual indicators
            updateRequirement('length-check', lengthMet);
            updateRequirement('uppercase-check', uppercaseMet);
            updateRequirement('lowercase-check', lowercaseMet);
            updateRequirement('number-check', numberMet);
            updateRequirement('special-check', specialMet);
            updateRequirement('match-check', matchMet);
            
            // Enable/disable reset button
            const allMet = lengthMet && uppercaseMet && lowercaseMet && numberMet && specialMet && matchMet;
            resetBtn.disabled = !allMet;
        }}
        
        function updateRequirement(elementId, isMet) {{
            const element = document.getElementById(elementId);
            const checkIcon = element.querySelector('.check-icon');
            
            if (isMet) {{
                element.className = 'requirement met';
                checkIcon.textContent = '✅';
            }} else {{
                element.className = 'requirement not-met';
                checkIcon.textContent = '❌';
            }}
        }}
        
        function resetPassword() {{
            const newPassword = document.getElementById('new_password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            // Final validation (should already be met due to button state)
            if (newPassword !== confirmPassword) {{
                alert('Passwords do not match. Please try again.');
                return;
            }}
            
            // Create form data
            const formData = new FormData();
            formData.append('token', '{token}');
            formData.append('new_password', newPassword);
            
            // Send POST request with form data
            fetch('/reset-password', {{
                method: 'POST',
                body: formData
            }})
            .then(response => response.json())
            .then(data => {{
                alert(data.message || 'Password reset successfully!');
                window.close();
            }})
            .catch(error => {{
                alert('Error resetting password');
                console.error('Error:', error);
            }});
        }}
        
        // Add event listeners for real-time validation
        document.getElementById('new_password').addEventListener('input', updateValidation);
        document.getElementById('confirm_password').addEventListener('input', updateValidation);
        
        // Initial validation
        updateValidation();
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)
@app.post("/reset-password")
async def reset_password(token: str = Form(...), new_password: str = Form(...)):
    """Reset password using reset token from form data"""
    # Find user with valid reset token
    user = await users_coll.find_one({
        "password_reset_token": token,
        "password_reset_expiry": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Hash new password
    new_password_hash = hash_pw(new_password)
    
    # Update password and clear reset token
    await users_coll.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "passwordHash": new_password_hash,
                "updatedAt": datetime.utcnow()
            },
            "$unset": {
                "password_reset_token": "",
                "password_reset_expiry": ""
            }
        }
    )
    
    return {"message": "Password reset successfully"}