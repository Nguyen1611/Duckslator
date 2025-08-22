from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import pipeline  # Import the pipeline's convert function
import time

app = FastAPI()

# Mount routers
try:
    from .authentication import auth_router as authentication_router
except ImportError:
    from authentication import auth_router as authentication_router  # type: ignore

try:
    from .jobs import router as jobs_router
except ImportError:
    from jobs import router as jobs_router  # type: ignore

app.include_router(authentication_router, prefix="/auth")
app.include_router(jobs_router)

# CORS (needed for cookie auth from Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary file name for backend processing
TEMP_INPUT_FILE = "input_video.mp4"
TEMP_OUTPUT_FILE = "output_video.mp4"

@app.post("/process-file/")
async def process_file(file: UploadFile = File(...), language: str = Form(...)):
    try:
        # Save the uploaded file temporarily
        with open(TEMP_INPUT_FILE, "wb") as f:
            f.write(await file.read())
        
        # Process the file using the pipeline
        pipeline.convert(TEMP_INPUT_FILE, language)
        
        # Return the processed video file
        if os.path.exists(TEMP_OUTPUT_FILE):
            return FileResponse(
                TEMP_OUTPUT_FILE,
                media_type="video/mp4",
                filename="translated_video.mp4"
            )
        else:
            return {"error": "Processed file not found."}
    
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
    finally:
        pass
        # # Clean up temporary files
        # time.sleep(180) # we can further improve by sending a signal to see if frontend has received then deleted

        # if os.path.exists(TEMP_INPUT_FILE):
        #     os.remove(TEMP_INPUT_FILE)
        # if os.path.exists(TEMP_OUTPUT_FILE):
        #     os.remove(TEMP_OUTPUT_FILE)
        #     os.remove('a.wav')
        #     os.remove('final_audio.wav')
        #     os.remove('transcript.json')