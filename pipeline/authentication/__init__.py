"""
Duckslator Authentication Package

This package provides comprehensive authentication functionality including:
- JWT token management
- Google OAuth integration
- User registration and login
- Password reset and email verification

Modules:
    - auth: Core JWT and password functions
    - google_auth: Google OAuth verification
    - authentication: All authentication endpoints
"""

from .auth import create_access_token, hash_pw, verify_pw
from .google_auth import verify_google_token
from .authentication import router as auth_router

__all__ = [
    "create_access_token",
    "hash_pw", 
    "verify_pw",
    "verify_google_token",
    "auth_router"
]