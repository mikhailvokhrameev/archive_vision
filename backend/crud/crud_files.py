# /crud/crud_files.py
from sqlalchemy.orm import Session
from models.file import File
from schemas.document import FileCreate
from typing import List
import uuid
from typing import List

def create_file(db: Session, file: FileCreate) -> File:
    db_file = File(
        file_name=file.file_name,
        file_path=file.file_path,
        file_extension=file.file_extension
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_file(db: Session, file_id: uuid.UUID) -> File:
    return db.query(File).filter(File.file_id == file_id).first()

def get_files(db: Session, skip: int = 0, limit: int = 100) -> List[File]:
    return db.query(File).offset(skip).limit(limit).all()
