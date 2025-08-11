# db.py
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise RuntimeError("Missing MONGODB_URI in .env")

client = AsyncIOMotorClient(MONGO_URI)

default_db = client.get_default_database()   # returns None if URI had no /dbname
db = default_db if default_db is not None else client["duckslator"]

users_coll = db["users"]
