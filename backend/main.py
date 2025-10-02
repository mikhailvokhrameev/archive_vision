import io
import json
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Path as FastApiPath
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from ocr import recognize_text_from_file

# Assuming these modules exist and function as before
# from ocr import recognize_text_from_file
from utils import save_upload_file

# Import new database functions
from database import (
    save_file_record,
    get_file_record,
    save_transcript_record,
    get_transcript_record,
    get_transcripts_for_file
)

# --- FastAPI Application Setup ---
app = FastAPI(
    title="Modular Document Transcription API",
    description="API for uploading files and managing their text transcripts.",
    version="2.0.0"
)

UPLOAD_DIR = Path("./data")
TRANSCRIPT_DIR = UPLOAD_DIR / "transcripts"
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

# --- API Endpoints ---

@app.post("/files/upload", summary="Upload a file and create its database record")
async def upload_file_endpoint(file: UploadFile = File(...)):
    """
    Receives a file, saves it to the server, and creates a record in the 'files' table.
    Returns the file's unique ID and metadata.
    """
    try:
        file_path = save_upload_file(file, str(UPLOAD_DIR))
        ext = Path(file.filename).suffix.lstrip('.')
        if not ext:
            raise HTTPException(status_code=400, detail="File must have an extension.")

        saved_record = save_file_record(
            file_path=file_path,
            file_name=file.filename,
            file_extension=ext
        )

        if saved_record is None:
            raise HTTPException(status_code=500, detail="Failed to save file record to the database.")

        return JSONResponse(content={
            "message": "File uploaded successfully.",
            "file_id": saved_record["file_id"],
            "file_name": file.filename,
            "load_date": saved_record["load_date"].isoformat()
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.post("/files/{file_id}/transcribe", summary="Generate a transcript for an existing file")
async def transcribe_file_endpoint(file_id: int = FastApiPath(..., description="The ID of the file to transcribe.")):
    """
    Finds a file by its ID, runs OCR, saves the transcript, and creates a record
    in the 'file_transcripts' table.
    """
    file_record = get_file_record(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found.")

    try:
        # Run OCR on the file
        extracted_text = recognize_text_from_file(file_record["file_path"])
        
        # Save the transcript to a text file
        transcript_filename = f"{Path(file_record['file_name']).stem}_{file_id}.txt"
        transcript_path = TRANSCRIPT_DIR / transcript_filename
        transcript_path.write_text(extracted_text, encoding="utf-8")

        # Create a dummy WER JSON object
        wer_data = {"confidence": 0.95, "word_count": len(extracted_text.split())}

        # Save the transcript record to the database
        transcript_id = save_transcript_record(
            file_id=file_id,
            transcript_path=str(transcript_path),
            wer=wer_data
        )

        if transcript_id is None:
            raise HTTPException(status_code=500, detail="Failed to save transcript record.")

        return JSONResponse(content={
            "message": "Transcription successful.",
            "transcript_id": transcript_id,
            "file_id": file_id,
            "transcript_path": str(transcript_path),
            "text": extracted_text
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during transcription: {e}")

@app.get("/transcripts/{transcript_id}", summary="Retrieve a specific transcript record")
async def get_transcript_endpoint(transcript_id: int):
    """Fetches a transcript record by its ID."""
    record = get_transcript_record(transcript_id)
    if not record:
        raise HTTPException(status_code=404, detail="Transcript not found.")
    return record

@app.get("/files/{file_id}/transcripts", summary="List all transcripts for a file")
async def list_transcripts_for_file_endpoint(file_id: int):
    """Fetches all transcript records associated with a given file ID."""
    transcripts = get_transcripts_for_file(file_id)
    if not transcripts:
        return {"message": "No transcripts found for this file.", "file_id": file_id, "transcripts": []}
    return {"file_id": file_id, "transcripts": transcripts}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
