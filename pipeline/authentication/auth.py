# auth.py
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET   = os.getenv("JWT_SECRET",  "super-secret-123")   # put in .env later
JWT_ALGO     = "HS256"
JWT_EXPIRE_M = 60  # minutes

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_pw(pw: str) -> str:
    return pwd_ctx.hash(pw)

def verify_pw(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_access_token(data: dict, expires_minutes: int = JWT_EXPIRE_M):
    to_encode = data.copy()
    exp = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": exp})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGO)

def decode_token(tok: str):
    return jwt.decode(tok, JWT_SECRET, algorithms=[JWT_ALGO])
