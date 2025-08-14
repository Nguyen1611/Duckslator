# auth_frontend/test_main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add the Duckslator root to import pipeline/*
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.authentication.authentication import router as auth_router

app = FastAPI(title="Duckslator Authentication Test Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router WITH the prefix here
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/")
async def root():
    return {"message": "Authentication Test Server Running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)