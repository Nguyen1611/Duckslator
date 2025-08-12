"""
Duckslator API - Video and Audio Translation Service

This FastAPI application provides:
- User authentication (email/password + Google OAuth)
- Email verification system
- Password reset functionality
- File upload and job management
- Translation processing simulation

Author: Nam Tran
Version: 1.0.0
"""

from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, status, Form, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse, FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo import ReturnDocument
from dotenv import load_dotenv
from pipeline.authentication.auth import create_access_token, decode_token, hash_pw, verify_pw
from pipeline.database.connection import users_coll, db
from pipeline.database.models import Token, UserCreate, UserOut, GoogleAuthRequest, GoogleUserInfo
from fastapi import File, UploadFile
import os
import shutil
import uuid
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from pipeline.authentication.google_auth import verify_google_token
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import re

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# CONFIGURATION AND SETUP
# =============================================================================

# Directory for storing uploaded and processed files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize FastAPI application
app = FastAPI(
    title="Duckslator API",
    description="Video and Audio Translation Service with User Authentication",
    version="1.0.0"
)

# OAuth2 scheme for JWT token authentication
# auto_error=False allows us to fall back to cookie authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def generate_verification_token() -> str:
    """
    Generate a secure random token for email verification.
    
    Returns:
        str: A 32-character URL-safe random token
    """
    return secrets.token_urlsafe(32)

def generate_password_reset_token() -> str:
    """
    Generate a secure random token for password reset.
    
    Returns:
        str: A 32-character URL-safe random token
    """
    return secrets.token_urlsafe(32)

def validate_password_strength(password: str) -> dict:
    """
    Validate that a password meets all security requirements.
    
    Args:
        password (str): The password to validate
        
    Returns:
        dict: Contains 'valid' (bool) and 'message' (str) keys
        
    Password Requirements:
        - At least 8 characters long
        - At least one uppercase letter (A-Z)
        - At least one lowercase letter (a-z)
        - At least one number (0-9)
        - At least one special character (!@#$%^&*(),.?":{}|<>)
    """
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

# =============================================================================
# EMAIL FUNCTIONS
# =============================================================================

async def send_verification_email(email: str, token: str) -> bool:
    """
    Send email verification email to newly registered users.
    
    Args:
        email (str): User's email address
        token (str): Verification token to include in email
        
    Returns:
        bool: True if email sent successfully, False otherwise
        
    Note:
        Requires SMTP credentials in environment variables:
        - SMTP_SERVER (default: smtp.gmail.com)
        - SMTP_PORT (default: 587)
        - SENDER_EMAIL
        - SENDER_PASSWORD
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    
    if not sender_email or not sender_password:
        print("SMTP credentials not configured, skipping email send")
        return False
    
    # Create verification URL with token
    verification_url = f"http://127.0.0.1:8000/verify-email/{token}"
    
    # Email body with verification link
    body = f"""
    Welcome to Duckslator!
    
    Please verify your email by clicking this link:
    {verification_url}
    
    If you didn't create this account, please ignore this email.
    """
    
    # Create email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = "Verify your Duckslator account"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Connect to SMTP server and send email
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

async def send_password_reset_email(email: str, body: str) -> bool:
    """
    Send password reset email to users who forgot their password.
    
    Args:
        email (str): User's email address
        body (str): Email body content
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    
    if not sender_email or not sender_password:
        print("SMTP credentials not configured, skipping email send")
        return False
    
    # Create email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = "Password Reset - Duckslator"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Connect to SMTP server and send email
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

# =============================================================================
# AUTHENTICATION MIDDLEWARE
# =============================================================================

async def get_current_user(request: Request, token: Optional[str] = Depends(oauth2_scheme)):
    """
    Get the current authenticated user from JWT token.
    
    This function supports both header-based and cookie-based authentication:
    - First tries to get token from Authorization header
    - Falls back to 'access_token' cookie if header is missing
    
    Args:
        request (Request): FastAPI request object
        token (Optional[str]): JWT token from Authorization header
        
    Returns:
        dict: User document from database
        
    Raises:
        HTTPException: 401 if token is invalid/expired, 404 if user not found
    """
    try:
        # Try Authorization header first, then fall back to cookie
        if not token:
            token = request.cookies.get("access_token")
        if not token:
            raise ValueError("No token provided")
            
        # Decode and validate JWT token
        payload = decode_token(token)
        uid = payload.get("sub")
        if uid is None:
            raise ValueError("Invalid token payload")
            
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Fetch user from database
    user = await users_coll.find_one({"_id": ObjectId(uid)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# =============================================================================
# CORE API ENDPOINTS
# =============================================================================

@app.get("/", include_in_schema=False)
def root():
    """
    Root endpoint that redirects to API documentation.
    
    Returns:
        RedirectResponse: Redirects to /docs (Swagger UI)
    """
    return RedirectResponse(url="/docs")

@app.on_event("startup")
async def init_indexes() -> None:
    """
    Initialize database indexes on application startup.
    
    Creates indexes for:
    - Unique email constraint on users collection
    - User ID index on jobs collection for efficient queries
    """
    await users_coll.create_index("email", unique=True)
    await db.jobs.create_index("user_id")

# =============================================================================
# USER MANAGEMENT ENDPOINTS
# =============================================================================

@app.post("/register", response_model=UserOut)
async def register(payload: UserCreate):
    """
    Register a new user account.
    
    Creates a new user with email verification required before login.
    Password must meet strength requirements.
    
    Args:
        payload (UserCreate): User registration data
        
    Returns:
        UserOut: Created user information (without sensitive data)
        
    Raises:
        HTTPException: 400 if email already exists or password is weak
    """
    # Check if email already exists
    if await users_coll.find_one({"email": payload.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password strength
    password_validation = validate_password_strength(payload.password)
    if not password_validation["valid"]:
        raise HTTPException(status_code=400, detail=password_validation["message"])
    
    # Generate verification token and create user document
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
    
    # Insert user into database
    result = await users_coll.insert_one(doc)
    
    # Send verification email
    await send_verification_email(payload.email, verification_token)
    
    # Return user information (excluding sensitive data)
    return UserOut(
        id=str(result.inserted_id),
        firstName=doc["name"]["first"],
        lastName=doc["name"]["last"],
        email=doc["email"],
        email_verified=False
    )

@app.post("/login", response_model=Token)
async def login(response: Response, form: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user with email and password.
    
    Verifies credentials and returns JWT token. Also sets an HttpOnly cookie
    for browser-based authentication.
    
    Args:
        response (Response): FastAPI response object for setting cookies
        form (OAuth2PasswordRequestForm): Form containing username (email) and password
        
    Returns:
        Token: JWT access token and type
        
    Raises:
        HTTPException: 401 if credentials are invalid or email not verified
    """
    # Find user by email
    user = await users_coll.find_one({"email": form.username})
    if not user or not verify_pw(form.password, user["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email or password"
        )
    
    # Check if email is verified
    if not user.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Please verify your email before logging in"
        )
    
    # Create JWT token
    token = create_access_token({"sub": str(user["_id"]), "email": user["email"]})
    
    # Set HttpOnly cookie for browser authentication
    response.set_cookie(
        "access_token", 
        token, 
        httponly=True, 
        samesite="lax", 
        secure=False,  # Set True in production with HTTPS
        max_age=60 * 60
    )
    
    return Token(access_token=token)

@app.post("/auth/google", response_model=Token)
async def google_auth(request: GoogleAuthRequest, response: Response):
    """
    Authenticate user with Google OAuth.
    
    Verifies Google ID token and either logs in existing user or creates new account.
    Google users are automatically email verified. Sets HttpOnly cookie for authentication.
    
    Args:
        request (GoogleAuthRequest): Contains Google ID token
        response (Response): FastAPI response object for setting cookies
        
    Returns:
        Token: JWT access token and type
        
    Raises:
        HTTPException: 400 if email not verified with Google, 500 for other errors
    """
    try:
        # Verify Google ID token
        google_user = await verify_google_token(request.id_token)
        
        # Check if email is verified with Google
        if not google_user['email_verified']:
            raise HTTPException(
                status_code=400, 
                detail="Email not verified with Google"
            )
        
        # Check if user already exists
        existing_user = await users_coll.find_one({"email": google_user['email']})
        
        if existing_user:
            # Update existing user to ensure email_verified is True
            await users_coll.update_one(
                {"_id": existing_user["_id"]},
                {
                    "$set": {
                        "email_verified": True,
                        "google_id": google_user['sub'],
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            # Generate token for existing user
            token = create_access_token({
                "sub": str(existing_user["_id"]),
                "email": existing_user["email"]
            })
            
            # Set authentication cookie
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                samesite="lax",
                secure=False,  # Set True in production with HTTPS
                max_age=60 * 60,
            )
            return Token(access_token=token)
            
        else:
            # Create new user from Google information
            now = datetime.utcnow()
            names = google_user['name'].split(' ', 1)
            first_name = names[0] if names else "Unknown"
            last_name = names[1] if len(names) > 1 else ""
            
            # Create user document
            doc = {
                "google_id": google_user['sub'],
                "name": {"first": first_name, "last": last_name},
                "email": google_user['email'],
                "email_verified": True,  # Google users are pre-verified
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
            
            # Insert new user and generate token
            result = await users_coll.insert_one(doc)
            token = create_access_token({
                "sub": str(result.inserted_id), 
                "email": doc["email"]
            })
            
            # Set authentication cookie
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                samesite="lax",
                secure=False,  # Set True in production with HTTPS
                max_age=60 * 60,
            )
            return Token(access_token=token)
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Authentication failed")

@app.get("/me", response_model=UserOut)
async def me(current=Depends(get_current_user)):
    """
    Get current user's profile information.
    
    Args:
        current: Current authenticated user (injected by get_current_user)
        
    Returns:
        UserOut: User profile information (excluding sensitive data)
    """
    return UserOut(
        id=str(current["_id"]),
        firstName=current["name"]["first"],
        lastName=current["name"]["last"],
        email=current["email"],
    )

@app.post("/logout")
def logout():
    """
    Logout current user by clearing authentication cookie.
    
    Returns:
        JSONResponse: Success message
    """
    resp = JSONResponse({"message": "logged out"})
    resp.delete_cookie("access_token")
    return resp

# =============================================================================
# PASSWORD RESET ENDPOINTS
# =============================================================================

@app.post("/forgot-password")
async def forgot_password(email: str):
    """
    Request password reset for email/password users.
    
    Generates a secure reset token and sends reset email. Only works for
    email/password users, not Google OAuth users.
    
    Args:
        email (str): User's email address
        
    Returns:
        dict: Success message (doesn't reveal if email exists for security)
        
    Raises:
        HTTPException: 500 if email sending fails
    """
    # Find user by email
    user = await users_coll.find_one({"email": email})
    if not user:
        # Don't reveal if user exists or not (security best practice)
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Only allow password reset for email/password users, not Google users
    if user.get("auth_provider") == "google":
        return {"message": "Google users cannot reset password through this method"}
    
    # Generate reset token with 24-hour expiry
    reset_token = generate_password_reset_token()
    token_expiry = datetime.utcnow() + timedelta(hours=24)
    
    # Store reset token and expiry in database
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
    
    # Create reset URL and email body
    reset_url = f"http://127.0.0.1:8000/reset-password?token={reset_token}"
    body = f"""
    Password Reset Request
    
    You requested a password reset for your Duckslator account.
    
    Click this link to reset your password:
    {reset_url}
    
    This link expires in 24 hours.
    
    If you didn't request this, please ignore this email.
    """
    
    # Send password reset email
    email_sent = await send_password_reset_email(email, body)
    
    if email_sent:
        return {"message": "Password reset email sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send password reset email")

@app.get("/reset-password", include_in_schema=False)
async def reset_password_page(token: str):
    """
    Show password reset form page.
    
    This endpoint displays an HTML form for users to enter their new password.
    The form includes real-time password validation and submits to POST /reset-password.
    
    Args:
        token (str): Password reset token from email link
        
    Returns:
        HTMLResponse: Password reset form with validation
        
    Note:
        This endpoint is hidden from API documentation as it's for user interface only.
    """
    # Verify token is valid and not expired
    user = await users_coll.find_one({
        "password_reset_token": token,
        "password_reset_expiry": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        return {"error": "Invalid or expired reset token"}
    
    # Return HTML form with real-time password validation
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
            
            // Check each password requirement
            const lengthMet = newPassword.length >= 8;
            const uppercaseMet = /[A-Z]/.test(newPassword);
            const lowercaseMet = /[a-z]/.test(newPassword);
            const numberMet = /[0-9]/.test(newPassword);
            const specialMet = /[!@#$%^&*(),.?":{{}}|<>]/.test(newPassword);
            const matchMet = newPassword === confirmPassword && newPassword.length > 0;
            
            // Update visual indicators for each requirement
            updateRequirement('length-check', lengthMet);
            updateRequirement('uppercase-check', uppercaseMet);
            updateRequirement('lowercase-check', lowercaseMet);
            updateRequirement('number-check', numberMet);
            updateRequirement('special-check', specialMet);
            updateRequirement('match-check', matchMet);
            
            // Enable/disable reset button based on all requirements
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
            
            // Final validation check
            if (newPassword !== confirmPassword) {{
                alert('Passwords do not match. Please try again.');
                return;
            }}
            
            // Create form data for submission
            const formData = new FormData();
            formData.append('token', '{token}');
            formData.append('new_password', newPassword);
            
            // Submit password reset request
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
        
        // Initialize validation state
        updateValidation();
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.post("/reset-password", include_in_schema=False)
async def reset_password(token: str = Form(...), new_password: str = Form(...)):
    """
    Process password reset using reset token.
    
    Validates the reset token and updates the user's password.
    Clears the reset token after successful password change.
    
    Args:
        token (str): Password reset token from form
        new_password (str): New password to set
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 400 if token is invalid/expired
        
    Note:
        This endpoint is hidden from API documentation as it's for form processing only.
    """
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

# =============================================================================
# JOB MANAGEMENT ENDPOINTS
# =============================================================================

@app.post("/jobs")
async def create_job(
    file: UploadFile = File(...), 
    target_lang: str = Form(...),
    current=Depends(get_current_user)
):
    """
    Create a new translation job.
    
    Uploads a file and creates a job record in the database.
    File is saved temporarily with a job-specific filename.
    
    Args:
        file (UploadFile): Audio/video file to translate
        target_lang (str): Target language for translation
        current: Current authenticated user (injected)
        
    Returns:
        dict: Job information including ID and status
        
    Raises:
        HTTPException: 400 if file is invalid, 401 if not authenticated
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
    """
    Get all jobs for the current authenticated user.
    
    Returns jobs sorted by creation date (newest first).
    Includes download URLs for completed jobs.
    
    Args:
        current: Current authenticated user (injected)
        
    Returns:
        dict: List of jobs and total count
    """
    # Query jobs for current user, sorted by creation date
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

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str, current=Depends(get_current_user)):
    """
    Delete a specific job and its associated files.
    
    Removes the job from database and deletes input/output files from disk.
    Only allows deletion of user's own jobs.
    
    Args:
        job_id (str): ID of job to delete
        current: Current authenticated user (injected)
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if job not found, 401 if not authenticated
    """
    # Find job and verify ownership
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

# =============================================================================
# FILE PROCESSING ENDPOINTS
# =============================================================================

@app.get("/download/latest")
async def download_latest_result(current=Depends(get_current_user)):
    """
    Download the most recent completed job result.
    
    Finds the latest completed job for the current user and returns
    the result file for download. Automatically cleans up files after download.
    
    Args:
        current: Current authenticated user (injected)
        
    Returns:
        FileResponse: File download response
        
    Raises:
        HTTPException: 404 if no completed jobs found or files missing
    """
    # Find the most recent completed job for this user
    job = await db.jobs.find_one(
        {"user_id": current["_id"], "status": "completed"},
        sort=[("created_at", -1)]
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="No completed jobs found")
    
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
    
    # Create file response for download
    response = FileResponse(
        path=file_path, 
        filename=download_filename, 
        media_type="application/octet-stream"
    )
    
    # Schedule file cleanup after download
    asyncio.create_task(cleanup_job_files(str(job["_id"])))
    
    return response

@app.post("/simulate-latest-job-safe-copy")
async def simulate_latest_job_safe_copy(current=Depends(get_current_user)):
    """
    Simulate job processing by copying input file to output.
    
    This endpoint simulates the translation process by safely copying
    the input file to create a result file. Updates job status to completed.
    
    Args:
        current: Current authenticated user (injected)
        
    Returns:
        dict: Processing results including file sizes and download URL
        
    Raises:
        HTTPException: 404 if no queued jobs found, 500 if processing fails
    """
    # Find the most recent queued job for this user
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
    
    # Construct file paths
    input_path = os.path.join(UPLOAD_DIR, input_file)
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="Input file missing")
    
    # Generate result filename
    ext = os.path.splitext(input_file)[1]
    result_filename = f"job_{job_id}_result{ext}"
    result_path = os.path.join(UPLOAD_DIR, result_filename)
    
    # Safely copy file in chunks to avoid memory issues
    try:
        with open(input_path, 'rb') as src:
            with open(result_path, 'wb') as dst:
                # Copy in 64KB chunks for memory efficiency
                while True:
                    chunk = src.read(65536)
                    if not chunk:
                        break
                    dst.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copy failed: {str(e)}")
    
    # Verify file sizes match for integrity
    original_size = os.path.getsize(input_path)
    copied_size = os.path.getsize(result_path)
    
    if original_size != copied_size:
        raise HTTPException(status_code=500, detail=f"Copy verification failed: {original_size} != {copied_size}")
    
    # Update job status to completed
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

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

async def cleanup_job_files(job_id: str):
    """
    Clean up job files after download.
    
    Removes input and result files from disk after a delay to ensure
    download completes. Updates job record to mark files as deleted.
    
    Args:
        job_id (str): ID of job to clean up
    """
    try:
        # Small delay to ensure download completes
        await asyncio.sleep(2)
        
        # Find job in database
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            return
        
        # Collect files to delete
        files_to_delete = []
        if job.get("input_file_path"):
            files_to_delete.append(job["input_file_path"])
        if job.get("result_file_path"):
            files_to_delete.append(job["result_file_path"])
        
        # Remove files from disk
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

