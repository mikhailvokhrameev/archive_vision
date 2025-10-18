# /schemas/document.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

class FileBase(BaseModel):
    file_name: str
    file_extension: str

class FileCreate(FileBase):
    file_path: str

class FileInDB(FileBase):
    file_id: uuid.UUID
    load_date: datetime
    file_path: str

    class Config:
        from_attributes = True

class TranscriptData(BaseModel):
    # Структура для распознанного текста
    text: str
    coordinates: List[int] # [x1, y1, x2, y2]
    confidence: float

class RecognitionResult(BaseModel):
    wer: float
    recognized_words: List[TranscriptData]
    extracted_attributes: dict # {"ФИО": "Иванов И.И.", "дата": "01.01.1990"}

class CorrectionData(BaseModel):
    corrected_text: str
    # Можно добавить информацию о том, какой именно фрагмент исправлен
    fragment_id: Optional[int] = None

class CorrectionInDB(CorrectionData):
    correction_id: uuid.UUID
    file_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class TranscriptInDB(BaseModel):
    transcript_id: uuid.UUID
    file_id: uuid.UUID
    transcript_path: str
    wer: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True
