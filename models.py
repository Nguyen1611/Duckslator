# models.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import bcrypt

# User input schema
class UserCreate(BaseModel):
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    age: int
    email: EmailStr
    password: str

# What to return to frontend (no password)
class UserOut(BaseModel):
    id: str
    firstName: str
    lastName: str
    email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    
# Hash plain text password
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
