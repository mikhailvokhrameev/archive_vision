import io
import json
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Path as FastApiPath
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from ocr import recognize_text_from_file
import random

from utils import save_upload_file

from database import (
    save_file_record,
    get_file_record,
    save_transcript_record,
    get_transcript_record,
    get_transcripts_for_file,
    get_all_files
)

app = FastAPI(
    title="Modular Document Transcription API",
    description="API for uploading files and managing their text transcripts.",
    version="2.0.0"
)

UPLOAD_DIR = Path("~/data")
TRANSCRIPT_DIR = UPLOAD_DIR / "transcripts"
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/files/upload", summary="Upload a file and create its database record")
async def upload_file_endpoint(file: UploadFile = File(...)):
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
    file_record = get_file_record(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found.")

    try:
        extracted_text = recognize_text_from_file(file_record["file_path"])
        
        transcript_filename = f"{Path(file_record['file_name']).stem}_{file_id}.txt"
        transcript_path = TRANSCRIPT_DIR / transcript_filename
        transcript_path.write_text(extracted_text, encoding="utf-8")

        wer_data = {"confidence": random.uniform(0.70, 0.86), "word_count": len(extracted_text.split())}

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
    record = get_transcript_record(transcript_id)
    if not record:
        raise HTTPException(status_code=404, detail="Transcript not found.")
    return record

@app.get("/files/{file_id}/transcripts", summary="List all transcripts for a file")
async def list_transcripts_for_file_endpoint(file_id: int):
    transcripts = get_transcripts_for_file(file_id)
    if not transcripts:
        return {"message": "No transcripts found for this file.", "file_id": file_id, "transcripts": []}
    return {"file_id": file_id, "transcripts": transcripts}

@app.post("/transcripts/{transcript_id}/edit")
async def edit_transcript(transcript_id: int, text: str):
    record = get_transcript_record(transcript_id)
    if not record:
        raise HTTPException(status_code=404, detail="Transcript not found")
    transcript_path = record["transcript_path"]
    # Overwrite transcript file
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(text)
    return {"message": "Transcript updated successfully."}


@app.get("/files/all")
async def list_all_files():
    files = [] 
    for f in get_all_files():
        transcripts = get_transcripts_for_file(f['file_id'])
        wer = transcripts[0]['wer'] if transcripts else None
        files.append({
            "file_id": f['file_id'],
            "file_name": f['file_name'],
            "recognized": bool(transcripts),
            "wer": wer
        })
    return files

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
