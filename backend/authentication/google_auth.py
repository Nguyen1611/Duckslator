"""
Duckslator Google OAuth Authentication Module

This module handles Google OAuth 2.0 authentication by verifying Google ID tokens.
It provides secure verification of tokens issued by Google for your application.

Dependencies:
    - google-auth: For Google OAuth token verification
    - python-dotenv: For environment variable loading

Security Features:
    - Verifies token signature using Google's public keys
    - Checks token audience (client_id) to prevent token reuse
    - Validates token expiration automatically
    - Extracts verified user information from Google

Author: Nam Tran
Version: 1.0.0
"""

from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# GOOGLE OAUTH CONFIGURATION
# =============================================================================

# Google OAuth 2.0 Client ID from Google Cloud Console
# This must match the client ID configured in your Google Cloud project
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# Validate that required environment variable is set
if not GOOGLE_CLIENT_ID:
    raise RuntimeError(
        "Missing GOOGLE_CLIENT_ID in .env file. "
        "Please add your Google OAuth client ID to continue."
    )

# =============================================================================
# GOOGLE TOKEN VERIFICATION
# =============================================================================

async def verify_google_token(token: str) -> dict:
    """
    Verify a Google ID token and extract user information.
    
    This function verifies that a Google ID token is valid and was issued
    for your application. It performs several security checks:
    
    Security Checks:
        - Verifies token signature using Google's public keys
        - Validates token audience (client_id) matches your application
        - Checks token expiration time
        - Ensures token was issued by Google
    
    Args:
        token (str): Google ID token string to verify
        
    Returns:
        dict: Verified user information with the following keys:
            - sub (str): Google's unique user identifier
            - email (str): User's email address
            - email_verified (bool): Whether email is verified with Google
            - name (str): User's full name
            - picture (str, optional): URL to user's profile picture
            
    Raises:
        ValueError: If token is invalid, expired, or verification fails
        
    Example:
        >>> user_info = await verify_google_token("google_id_token_here")
        >>> print(f"User: {user_info['name']} ({user_info['email']})")
        User: John Doe (john.doe@gmail.com)
        
    Usage:
        This function is typically called after receiving an ID token from
        the Google Sign-In flow on the frontend. The returned information
        can be used to create or authenticate users in your system.
        
    Security Notes:
        - Never trust ID tokens without verification
        - Always verify the client_id matches your application
        - Check email_verified status for additional security
        - Tokens have a limited lifespan (typically 1 hour)
    """
    try:
        # Verify the OAuth 2.0 ID token using Google's verification service
        # This performs all security checks including signature verification
        info = id_token.verify_oauth2_token(
            token,                    # The ID token to verify
            requests.Request(),        # HTTP request object for verification
            GOOGLE_CLIENT_ID,         # Your application's client ID
        )
        
        # Extract and return verified user information
        # Only return fields that are guaranteed to be present and verified
        return {
            "sub": info["sub"],                           # Google's unique user ID
            "email": info["email"],                       # User's email address
            "email_verified": info.get("email_verified", False),  # Email verification status
            "name": info.get("name", ""),                 # User's display name
            "picture": info.get("picture"),               # Profile picture URL (optional)
        }
        
    except Exception as e:
        # Re-raise as ValueError with descriptive message
        # This allows calling code to handle verification failures gracefully
        raise ValueError(f"Invalid Google ID token: {e}")