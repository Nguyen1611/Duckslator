from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv
import os

load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise RuntimeError("Missing GOOGLE_CLIENT_ID in .env")

async def verify_google_token(token: str) -> dict:
    """
    Verifies a Google ID token issued for your client_id.
    Returns dict with: sub, email, email_verified, name, picture.
    Raises ValueError on invalid token.
    """
    try:
        info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID,
        )
        return {
            "sub": info["sub"],
            "email": info["email"],
            "email_verified": info.get("email_verified", False),
            "name": info.get("name", ""),
            "picture": info.get("picture"),
        }
    except Exception as e:
        raise ValueError(f"Invalid token: {e}")