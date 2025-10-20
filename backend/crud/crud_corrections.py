# /crud/crud_corrections.py
from sqlalchemy.orm import Session
from models.file import FileCorrection
from schemas.document import CorrectionData
import uuid

def create_correction(db: Session, file_id: uuid.UUID, correction: CorrectionData) -> FileCorrection:
    db_correction = FileCorrection(
        file_id=file_id,
        corrected_text=correction.corrected_text,
        fragment_id=correction.fragment_id
    )
    db.add(db_correction)
    db.commit()
    db.refresh(db_correction)
    return db_correction
