# /crud/crud_transcripts.py
from sqlalchemy.orm import Session
from models.file import FileTranscript
from typing import List
import uuid
from typing import List

def create_file_transcript(db: Session, file_id: uuid.UUID, transcript_path: str, wer: float):
    db_transcript = FileTranscript(
        file_id=file_id,
        transcript_path=transcript_path,
        wer={"wer": wer}
    )
    db.add(db_transcript)
    db.commit()
    db.refresh(db_transcript)
    return db_transcript

def get_total_processed_count(db: Session) -> int:
    return db.query(FileTranscript).count()

def get_transcript_by_file_id(db: Session, file_id: uuid.UUID) -> FileTranscript:
    return db.query(FileTranscript).filter(FileTranscript.file_id == file_id).first()

def get_transcripts(db: Session, skip: int = 0, limit: int = 100) -> List[FileTranscript]:
    return db.query(FileTranscript).offset(skip).limit(limit).all()
