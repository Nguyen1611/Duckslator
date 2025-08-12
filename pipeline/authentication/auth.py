"""
Duckslator Authentication Module

This module provides core authentication functionality including:
- Password hashing and verification using bcrypt
- JWT token creation and validation
- Secure password handling with configurable expiration

Dependencies:
    - python-jose[cryptography]: For JWT operations
    - passlib[bcrypt]: For password hashing
    - python-dotenv: For environment variable loading

Author: Nam Tran
Version: 1.0.0
"""

from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# JWT CONFIGURATION
# =============================================================================

# JWT secret key for signing tokens (should be stored in .env file)
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-123")

# JWT algorithm for token signing (HS256 is secure and widely supported)
JWT_ALGO = "HS256"

# Default token expiration time in minutes
JWT_EXPIRE_M = 60  # 1 hour

# =============================================================================
# PASSWORD CONTEXT
# =============================================================================

# Initialize password hashing context using bcrypt
# bcrypt is a secure, adaptive hashing algorithm that automatically handles salt generation
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =============================================================================
# PASSWORD FUNCTIONS
# =============================================================================

def hash_pw(pw: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    This function generates a secure hash of the provided password.
    The hash includes a random salt and is designed to be computationally expensive
    to prevent brute force attacks.
    
    Args:
        pw (str): Plain text password to hash
        
    Returns:
        str: Bcrypt hash of the password (includes salt)
        
    Example:
        >>> hashed = hash_pw("myPassword123")
        >>> hashed.startswith("$2b$")
        True
    """
    return pwd_ctx.hash(pw)

def verify_pw(plain: str, hashed: str) -> bool:
    """
    Verify a plain text password against its hash.
    
    This function securely compares a plain text password with a previously
    generated hash. It handles salt extraction and comparison automatically.
    
    Args:
        plain (str): Plain text password to verify
        hashed (str): Previously generated password hash
        
    Returns:
        bool: True if password matches hash, False otherwise
        
    Example:
        >>> hashed = hash_pw("myPassword123")
        >>> verify_pw("myPassword123", hashed)
        True
        >>> verify_pw("wrongPassword", hashed)
        False
    """
    return pwd_ctx.verify(plain, hashed)

# =============================================================================
# JWT TOKEN FUNCTIONS
# =============================================================================

def create_access_token(data: dict, expires_minutes: int = JWT_EXPIRE_M) -> str:
    """
    Create a new JWT access token.
    
    This function creates a JSON Web Token that contains user information
    and an expiration timestamp. The token is signed with the JWT secret key.
    
    Args:
        data (dict): Data to encode in the token (typically user ID and email)
        expires_minutes (int, optional): Token expiration time in minutes. 
                                       Defaults to JWT_EXPIRE_M (60 minutes)
        
    Returns:
        str: JWT token string
        
    Example:
        >>> token = create_access_token({"sub": "user123", "email": "user@example.com"})
        >>> len(token) > 100  # JWT tokens are typically long
        True
        
    Security Notes:
        - Tokens are automatically expired after the specified time
        - The 'exp' claim is automatically added to prevent token reuse
        - Tokens are signed with HMAC-SHA256 for integrity
    """
    # Create a copy of the data to avoid modifying the original
    to_encode = data.copy()
    
    # Calculate expiration time
    exp = datetime.utcnow() + timedelta(minutes=expires_minutes)
    
    # Add expiration claim to token data
    to_encode.update({"exp": exp})
    
    # Encode and sign the JWT token
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGO)

def decode_token(tok: str) -> dict:
    """
    Decode and verify a JWT token.
    
    This function decodes a JWT token, verifies its signature, and checks
    if it has expired. It returns the token payload if valid.
    
    Args:
        tok (str): JWT token string to decode
        
    Returns:
        dict: Decoded token payload containing user data and claims
        
    Raises:
        JWTError: If token is invalid, expired, or signature verification fails
        
    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> payload = decode_token(token)
        >>> payload["sub"]
        'user123'
        
    Security Notes:
        - Automatically verifies token signature using JWT_SECRET
        - Checks expiration time and rejects expired tokens
        - Uses the same algorithm (HS256) that was used for signing
    """
    return jwt.decode(tok, JWT_SECRET, algorithms=[JWT_ALGO])