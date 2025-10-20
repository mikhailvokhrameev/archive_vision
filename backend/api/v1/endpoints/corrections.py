# /backend/api/v1/endpoints/corrections.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
import uuid
import json
import os

from schemas.document import CorrectionData
from core.config import settings
from core.database import get_db
from crud import crud_files

router = APIRouter()

@router.post("/{file_id}/corrections", status_code=201)
def save_corrections(
    file_id: uuid.UUID,
    corrections: List[CorrectionData],
    db: Session = Depends(get_db)
):
    """
    Save a list of corrections for a given file.
    The corrections are saved into a JSON file.
    """
    # 1. Verify the file exists
    db_file = crud_files.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")

    # 2. Define the output path for the corrections file
    corrections_dir = settings.CORRECTIONS_DIRECTORY
    if not os.path.exists(corrections_dir):
        os.makedirs(corrections_dir)
    
    corrections_filename = f"{file_id}_corrections.json"
    corrections_path = os.path.join(corrections_dir, corrections_filename)

    # 3. Save the corrections to the JSON file
    try:
        # Convert Pydantic models to a list of dictionaries
        corrections_data = [c.model_dump() for c in corrections]
        
        with open(corrections_path, "w", encoding="utf-8") as f:
            json.dump(corrections_data, f, indent=4, ensure_ascii=False)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save corrections file: {str(e)}")

    return {"message": "Corrections saved successfully", "path": corrections_path}
