"""
Duckslator Data Models

This module defines Pydantic models for data validation and serialization.
These models ensure data integrity and provide clear interfaces for API endpoints.

Models include:
    - GoogleAuthRequest: For Google OAuth authentication requests
    - GoogleUserInfo: For verified Google user information
    - UserCreate: For user registration requests
    - UserOut: For user profile responses (excludes sensitive data)
    - Token: For authentication token responses

Dependencies:
    - pydantic: For data validation and serialization
    - pydantic[email]: For email validation
    - bcrypt: For password hashing (legacy function)

Author: Nam Tran
Version: 1.0.0
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import bcrypt

# =============================================================================
# GOOGLE OAUTH MODELS
# =============================================================================

class GoogleAuthRequest(BaseModel):
    """
    Request model for Google OAuth authentication.
    
    This model validates the structure of Google authentication requests
    sent from the frontend after Google Sign-In.
    
    Fields:
        id_token (str): Google ID token received from Google Sign-In flow
    """
    id_token: str = Field(
        ..., 
        description="Google ID token from OAuth flow",
        min_length=1,
        example="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
    )

class GoogleUserInfo(BaseModel):
    """
    Verified Google user information.
    
    This model represents user data extracted from a verified Google ID token.
    All fields are guaranteed to be authentic as they come from Google's
    verification service.
    
    Fields:
        email (EmailStr): User's verified email address
        email_verified (bool): Whether email is verified with Google
        name (str): User's full name from Google profile
        picture (Optional[str]): URL to user's profile picture
        sub (str): Google's unique user identifier
    """
    email: EmailStr = Field(..., description="User's email address")
    email_verified: bool = Field(..., description="Email verification status")
    name: str = Field(..., description="User's full name", min_length=1)
    picture: Optional[str] = Field(None, description="Profile picture URL")
    sub: str = Field(..., description="Google's unique user identifier")

# =============================================================================
# USER MANAGEMENT MODELS
# =============================================================================

class UserCreate(BaseModel):
    """
    User registration request model.
    
    This model validates user registration data before creating new accounts.
    It includes validation rules and field aliases for frontend compatibility.
    
    Fields:
        first_name (str): User's first name (aliased as "firstName")
        last_name (str): User's last name (aliased as "lastName")
        age (int): User's age (must be positive)
        email (EmailStr): User's email address (automatically validated)
        password (str): User's password (will be hashed before storage)
        
    Validation Rules:
        - Names must be non-empty strings
        - Age must be positive integer
        - Email must be valid format
        - Password must be provided
    """
    first_name: str = Field(
        ..., 
        alias="firstName",
        description="User's first name",
        min_length=1,
        max_length=50,
        example="John"
    )
    last_name: str = Field(
        ..., 
        alias="lastName",
        description="User's last name",
        min_length=1,
        max_length=50,
        example="Doe"
    )
    age: int = Field(
        ..., 
        description="User's age",
        gt=0,
        le=120,
        example=25
    )
    email: EmailStr = Field(
        ..., 
        description="User's email address",
        example="john.doe@example.com"
    )
    password: str = Field(
        ..., 
        description="User's password",
        min_length=8,
        example="SecurePass123!"
    )
    
    @validator('password')
    def validate_password_strength(cls, v):
        """
        Validate password meets security requirements.
        
        Ensures password contains:
        - At least 8 characters
        - Mix of uppercase, lowercase, numbers, and special characters
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
            
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
            
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
            
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in v):
            raise ValueError('Password must contain at least one special character')
            
        return v

class UserOut(BaseModel):
    """
    User profile response model.
    
    This model represents user data returned to the frontend.
    It excludes sensitive information like passwords and internal fields.
    
    Fields:
        id (str): User's unique identifier
        firstName (str): User's first name
        lastName (str): User's last name
        email (EmailStr): User's email address
        email_verified (bool): Whether email has been verified
        
    Security Notes:
        - No password or internal database fields are exposed
        - Safe to return to frontend without additional filtering
    """
    id: str = Field(..., description="User's unique identifier")
    firstName: str = Field(..., description="User's first name")
    lastName: str = Field(..., description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    email_verified: bool = Field(
        default=False, 
        description="Whether user's email has been verified"
    )

# =============================================================================
# AUTHENTICATION MODELS
# =============================================================================

class Token(BaseModel):
    """
    Authentication token response model.
    
    This model represents the response when users successfully authenticate.
    It follows the OAuth 2.0 standard for token responses.
    
    Fields:
        access_token (str): JWT token for API authentication
        token_type (str): Token type, defaults to "bearer"
        
    Usage:
        Returned by login and OAuth endpoints to provide access credentials.
        The access_token should be included in subsequent API requests.
    """
    access_token: str = Field(..., description="JWT access token for authentication")
    token_type: str = Field(
        default="bearer", 
        description="Token type (OAuth 2.0 standard)",
        example="bearer"
    )

# =============================================================================
# LEGACY FUNCTIONS
# =============================================================================

def hash_password(plain: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    This is a legacy function that provides the same functionality as
    the hash_pw function in auth.py. It's kept for backward compatibility.
    
    Args:
        plain (str): Plain text password to hash
        
    Returns:
        str: Bcrypt hash of the password
        
    Note:
        This function is deprecated. Use hash_pw from auth.py instead.
    """
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# Configure Pydantic models for optimal performance and validation
class Config:
    """Pydantic model configuration."""
    
    # Allow field aliases for frontend compatibility
    allow_population_by_field_name = True
    
    # Validate field types strictly
    validate_assignment = True
    
    # Use enum values for validation
    use_enum_values = True