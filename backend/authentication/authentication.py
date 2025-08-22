"""
Duckslator Authentication Routes

This module contains all authentication-related endpoints organized into logical groups:
- REGISTER/LOGIN: User registration, login, email verification, logout
- GOOGLE AUTH: Google OAuth authentication
- PASSWORD RESET: Password reset functionality
- USER PROFILE: User profile management

Dependencies:
    - FastAPI: For API endpoints and request/response handling
    - Motor: For async MongoDB operations
    - JWT: For token-based authentication
    - SMTP: For email functionality

Author: Nam Tran
Version: 1.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
import os
import secrets
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import asyncio
from bson import ObjectId
from jose import jwt, JWTError

# Import local modules
from .auth import create_access_token, hash_pw, verify_pw, JWT_SECRET, JWT_ALGO
from .google_auth import verify_google_token
from ..database.connection import users_coll
from ..database.models import UserCreate, UserOut, Token, GoogleAuthRequest

# =============================================================================
# ROUTER SETUP
# =============================================================================

# Create router for authentication endpoints
router = APIRouter(tags=["Authentication"])

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def validate_password_strength(password: str) -> bool:
    if len(password) < 8:
        return False
    
    if not re.search(r'[A-Z]', password):
        return False
        
    if not re.search(r'[a-z]', password):
        return False
        
    if not re.search(r'\d', password):
        return False
        
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
        
    return True

def generate_verification_token() -> str:
    """Generate a secure verification token for email verification."""
    return secrets.token_urlsafe(32)

def generate_password_reset_token() -> str:
    """Generate a secure password reset token."""
    return secrets.token_urlsafe(32)

# =============================================================================
# EMAIL FUNCTIONS
# =============================================================================

async def send_verification_email(email: str, token: str) -> bool:
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in {"1", "true", "yes"}
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        print("SMTP credentials not configured, skipping email send")
        return False

    # Build verification link from environment when provided
    backend_base = os.getenv("BACKEND_BASE_URL")  # e.g., http://127.0.0.1:8001
    if backend_base:
        backend_base = backend_base.rstrip("/")
        verification_link = f"{backend_base}/auth/verify-email/{token}"
    else:
        verification_link = f"http://127.0.0.1:8001/auth/verify-email/{token}"
    
    body = f"""
    Welcome to Duckslator!
    
    Please verify your email address by clicking the link below:
    {verification_link}
    
    This link will expire in 24 hours.
    
    If you didn't create an account, please ignore this email.
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = "Verify Your Duckslator Account"
    msg.attach(MIMEText(body, 'plain'))

    # Retry send a few times for better reliability
    last_error = None
    for attempt_index in range(3):
        try:
            if smtp_use_ssl or smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_server, int(os.getenv("SMTP_PORT", "465"))) as server:
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
            print(f"Verification email sent to {email} (attempt {attempt_index + 1})")
            return True
        except Exception as e:
            last_error = e
            print(f"Attempt {attempt_index + 1} to send verification email failed: {e}")
            # brief backoff then retry
            await asyncio.sleep(1.0 + attempt_index)
    print(f"Failed to send verification email to {email} after retries: {last_error}")
    return False

async def send_password_reset_email(email: str, token: str) -> bool:
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        print("SMTP credentials not configured, skipping email send")
        return False

    # Build reset link to the frontend (Option A)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    reset_link = f"{frontend_url}/reset-password?token={token}"

    subject = "Reset Your Duckslator Password"
    body = f"""
    Hi,

    You requested to reset your Duckslator password.

    Click the link below to set a new password:
    {reset_link}

    If you didn't request this, you can safely ignore this email.
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject
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

# =============================================================================
# AUTHENTICATION MIDDLEWARE
# =============================================================================

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> dict:
    """
    Extract and validate JWT token from request.
    
    This function supports both header-based and cookie-based authentication:
    - First checks Authorization header (Bearer token)
    - Falls back to access_token cookie if header is missing
    
    Args:
        request (Request): FastAPI request object
        token (str, optional): JWT token from Authorization header
        
    Returns:
        dict: User data from token
        
    Raises:
        HTTPException: 401 if token is invalid or missing
    """
    print(f"get_current_user called - token from header: {token}")
    print(f"Cookies: {request.cookies}")
    
    if token:
        # Token provided in Authorization header
        print(f"Using token from Authorization header: {token[:20]}...")
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            user_id = payload.get("sub")
            print(f"Decoded payload: {payload}")
            if user_id is None:
                print("No user_id in payload")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except JWTError as e:
            print(f"JWT decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        # Try to get token from cookie
        token = request.cookies.get("access_token")
        print(f"Token from cookie: {token[:20] if token else 'None'}...")
        if not token:
            print("No token in cookie")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            user_id = payload.get("sub")
            print(f"Decoded cookie payload: {payload}")
            if user_id is None:
                print("No user_id in cookie payload")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except JWTError as e:
            print(f"JWT decode error from cookie: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Get user from database
    print(f"Looking for user with ID: {user_id}")
    user = await users_coll.find_one({"_id": ObjectId(user_id)})
    if user is None:
        print(f"User not found in database for ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"User found: {user.get('email', 'No email')}")
    return user

# =============================================================================
# GROUP 1: REGISTER/LOGIN ENDPOINTS
# =============================================================================

@router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    """
    Register a new user account.
    
    Creates a new user account with email verification required.
    Password is hashed before storage. Verification email is sent automatically.
    """
    # Validate password strength
    if not validate_password_strength(user_data.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters and contain uppercase, lowercase, number, and special character"
        )
    
    # Check if user already exists
    existing_user = await users_coll.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="User with this email already exists"
        )
    
    # Hash password
    hashed_password = hash_pw(user_data.password)
    
    # Generate verification token
    verification_token = generate_verification_token()
    
    # Create user document
    user_doc = {
        "email": user_data.email,
        "passwordHash": hashed_password,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "age": user_data.age,
        "email_verified": False,
        "verification_token": verification_token,
        "auth_provider": "email",
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    
    # Insert user into database
    await users_coll.insert_one(user_doc)
    
    # Send verification email now to guarantee delivery
    sent = await send_verification_email(user_data.email, verification_token)
    if not sent:
        # Do not fail registration, but inform logs; user can still use resend endpoint
        print(f"Warning: initial verification email could not be sent to {user_data.email}")
    
    return {"message": "User registered successfully. Please check your email to verify your account."}

@router.post("/login", response_model=Token)
async def login(
    email: str = Form(...),
    password: str = Form(...),
    response: Response = None
):
    """
    Authenticate user with email and password.
    
    Verifies user credentials and returns JWT token.
    Sets HttpOnly cookie for automatic authentication.
    """
    # Find user by email
    user = await users_coll.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_pw(password, user["passwordHash"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Check if email is verified
    if not user.get("email_verified", False):
        raise HTTPException(
            status_code=401,
            detail="Please verify your email before logging in"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "email": user["email"]}
    )
    
    # Set HttpOnly cookie
    if response:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=3600
        )
    
    return Token(access_token=access_token)

@router.post("/logout")
async def logout(response: Response):
    """
    Logout user by clearing authentication cookie.
    """
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}

@router.get("/verify-email/{token}")
async def verify_email(token: str):
    """
    Verify user email using verification token.
    """
    # Find user with verification token
    user = await users_coll.find_one({"verification_token": token})
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification token"
        )
    
    # Update user to mark email as verified
    await users_coll.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"email_verified": True},
            "$unset": {"verification_token": ""}
        }
    )
    
    return {"message": "Email verified successfully. You can now log in."}

@router.post("/resend-verification-email")
async def resend_verification_email(email: str):
    """
    Resend verification email to user.
    """
    # Find user by email
    user = await users_coll.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=400,
            detail="User not found"
        )
    
    if user.get("email_verified", False):
        raise HTTPException(
            status_code=400,
            detail="Email is already verified"
        )
    
    # Generate new verification token
    verification_token = generate_verification_token()
    
    # Update user with new token
    await users_coll.update_one(
        {"_id": user["_id"]},
        {"$set": {"verification_token": verification_token}}
    )
    
    # Send new verification email
    await send_verification_email(email, verification_token)
    
    return {"message": "Verification email sent successfully"}

# =============================================================================
# GROUP 2: GOOGLE AUTH ENDPOINTS
# =============================================================================

@router.get("/google/start")
async def google_auth_start():
    """
    Start Google OAuth flow.
    
    Redirects user to Google OAuth consent screen.
    """
    # Google OAuth configuration
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/auth/google/callback")
    
    if not google_client_id:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured"
        )
    
    # Google OAuth scopes
    scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
    
    # Build Google OAuth URL
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={google_client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={'%20'.join(scopes)}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return {"auth_url": google_auth_url}

@router.get("/google/callback")
async def google_auth_callback(code: str, response: Response):
    """
    Handle Google OAuth callback.
    
    Receives authorization code from Google and exchanges it for user info.
    """
    try:
        # Exchange code for tokens
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/auth/google/callback")
        
        if not google_client_id or not google_client_secret:
            raise HTTPException(
                status_code=500,
                detail="Google OAuth not configured"
            )
        
        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": google_client_id,
            "client_secret": google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        import httpx
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
        
        # Get user info using access token
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(userinfo_url, headers=headers)
            userinfo_response.raise_for_status()
            google_user = userinfo_response.json()
        
        # Check if user already exists
        existing_user = await users_coll.find_one({"email": google_user['email']})
        
        if existing_user:
            # Update existing user
            await users_coll.update_one(
                {"_id": existing_user["_id"]},
                {
                    "$set": {
                        "email_verified": True,
                        "google_id": google_user['id'],
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            # Generate token for existing user
            token = create_access_token({
                "sub": str(existing_user["_id"]),
                "email": existing_user["email"]
            })
        else:
            # Create new user from Google information
            now = datetime.utcnow()
            names = google_user['name'].split(' ', 1)
            first_name = names[0] if names else "Unknown"
            last_name = names[1] if len(names) > 1 else ""
            
            # Create user document
            doc = {
                "google_id": google_user['id'],
                "first_name": first_name,
                "last_name": last_name,
                "email": google_user['email'],
                "email_verified": True,  # Google users are pre-verified
                "picture": google_user.get('picture'),
                "auth_provider": "google",
                "created_at": now,
                "updated_at": now,
            }
            
            # Insert new user and generate token
            result = await users_coll.insert_one(doc)
            token = create_access_token({
                "sub": str(result.inserted_id),
                "email": doc["email"]
            })
        
        # Redirect to frontend with success and token
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}/oauth-callback?auth=success&token={token}",
            status_code=302
        )
        
    except Exception as e:
        print(f"Google OAuth error: {e}")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}/oauth-callback?auth=error",
            status_code=302
        )

@router.post("/google", response_model=Token)
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

# =============================================================================
# GROUP 3: PASSWORD RESET ENDPOINTS
# =============================================================================

@router.post("/forgot-password")
async def forgot_password(email: str):
    """
    Initiate password reset process.

    Generates password reset token and sends reset email.
    Only works for email/password users, not Google users.
    """
    # Find user by email
    user = await users_coll.find_one({"email": email})
    if not user:
        # Don't reveal if user exists for security
        return {"message": "If an account exists with this email, a password reset link has been sent."}

    # Check if user is Google user
    if user.get("auth_provider") == "google":
        return {"message": "Google users cannot reset passwords through this method."}

    # Generate password reset token
    reset_token = generate_password_reset_token()

    # Store token with expiration (24 hours)
    await users_coll.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_reset_token": reset_token,
                "password_reset_expiry": datetime.utcnow() + timedelta(hours=24)
            }
        }
    )

    # Send password reset email (function will build the link using FRONTEND_URL)
    await send_password_reset_email(email, reset_token)

    return {"message": "If an account exists, a password reset link has been sent."}

@router.post("/reset-password")
async def reset_password(token: str = Form(...), new_password: str = Form(...)):
    """
    Complete password reset using token from email.
    """
    # Find user by token
    user = await users_coll.find_one({"password_reset_token": token})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    print(f"Found user: {user['email']}")
    print(f"Token: {token}")
    print(f"Expiry field: {user.get('password_reset_expiry')}")
    print(f"Current time: {datetime.utcnow()}")
    # Check expiry (note: your schema uses 'password_reset_expiry' not 'password_reset_expires')
    expires = user.get("password_reset_expiry")
    if not expires or datetime.utcnow() > expires:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    # Validate password strength
    if not validate_password_strength(new_password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 chars, include upper, lower, number, and special character"
        )
    
    # Hash new password and update database
    hashed_password = hash_pw(new_password)
    
    await users_coll.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "passwordHash": hashed_password,  
                "updatedAt": datetime.utcnow()
            },
            "$unset": {
                "password_reset_token": "",
                "password_reset_expiry": ""  
            }
        }
    )
    
    return {"message": "Password has been updated successfully"}

@router.get("/validate-reset-token")
async def validate_reset_token(token: str):
    """
    Validate password reset token without resetting password.
    
    Frontend can use this to check if token is valid before showing reset form.
    """
    # Find user with valid token
    user = await users_coll.find_one({
        "password_reset_token": token,
        "password_reset_expiry": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        return {"valid": False, "message": "Invalid or expired reset token"}
    
    return {"valid": True, "message": "Token is valid", "email": user["email"]}

# =============================================================================
# GROUP 4: USER PROFILE ENDPOINTS
# =============================================================================

@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user's profile information.
    
    Args:
        current_user (dict): Current authenticated user from middleware
        
    Returns:
        UserOut: User profile information
    """
    return UserOut(
        id=str(current_user["_id"]),
        firstName=current_user.get("first_name", ""),
        lastName=current_user.get("last_name", ""),
        email=current_user["email"],
        email_verified=current_user.get("email_verified", False)
    )

@router.get("/test-auth")
async def test_auth(request: Request):
    """
    Test endpoint to check authentication status and cookies.
    """
    cookies = request.cookies
    auth_header = request.headers.get("authorization")
    
    print(f"=== TEST AUTH DEBUG ===")
    print(f"All headers: {dict(request.headers)}")
    print(f"Cookies: {dict(cookies)}")
    print(f"Auth header: {auth_header}")
    print(f"Host: {request.headers.get('host')}")
    print(f"Origin: {request.headers.get('origin')}")
    print(f"Referer: {request.headers.get('referer')}")
    print(f"=======================")
    
    return {
        "cookies": dict(cookies),
        "auth_header": auth_header,
        "user_agent": request.headers.get("user-agent"),
        "host": request.headers.get("host"),
        "origin": request.headers.get("origin"),
        "all_headers": dict(request.headers),
    }

