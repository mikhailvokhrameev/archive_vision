# /api/v1/endpoints/documents.py
import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from core.database import get_db
from core.config import settings
from crud import crud_files, crud_transcripts, crud_corrections
from schemas.document import FileCreate, FileInDB, CorrectionData, TranscriptInDB, TranscriptInDB
from services import ocr_service

router = APIRouter()

@router.on_event("startup")
def startup_event():
    os.makedirs(settings.UPLOADS_DIRECTORY, exist_ok=True)
    os.makedirs(settings.TRANSCRIPTS_DIRECTORY, exist_ok=True)
    os.makedirs(settings.CORRECTIONS_DIRECTORY, exist_ok=True)

@router.post("/upload", response_model=List[FileInDB], status_code=201)
def upload_documents(
    files: List[UploadFile] = File(...), 
    db: Session = Depends(get_db)
):
    """
    1-3) Загрузка одного или нескольких документов на сервер и сохранение в БД.
    Поддерживаемые форматы: JPG, JPEG, TIFF, PDF.
    """
    allowed_extensions = {"jpg", "jpeg", "tiff", "pdf"}
    uploaded_files = []
    
    for file in files:
        extension = file.filename.split('.')[-1].lower()
        if extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Файлы с расширением {extension} не поддерживаются.")
        
        # Генерируем уникальное имя файла
        unique_filename = f"{uuid.uuid4()}.{extension}"
        file_path = os.path.join(settings.UPLOADS_DIRECTORY, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_data = FileCreate(
            file_name=file.filename,
            file_path=file_path,
            file_extension=extension
        )
        db_file = crud_files.create_file(db=db, file=file_data)
        uploaded_files.append(db_file)
        
    return uploaded_files

def process_and_save_results(db: Session, file_id: uuid.UUID, file_path: str):
    """
    Функция для фоновой задачи: запускает OCR и сохраняет результат.
    4, 5, 10) Нормализация, извлечение данных и сохранение в БД.
    """
    transcript_path, wer = ocr_service.process_document_mock(file_id, file_path)
    crud_transcripts.create_file_transcript(db, file_id, transcript_path, wer)

@router.post("/{file_id}/process", status_code=202)
def process_document(
    file_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Запускает асинхронную обработку документа.
    """
    db_file = crud_files.get_file(db, file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    background_tasks.add_task(process_and_save_results, db, file_id, db_file.file_path)
    
    return {"message": "Обработка документа запущена в фоновом режиме."}

@router.get("/process-status/{file_id}")
def get_process_status(file_id: uuid.UUID):
    """
    6) Эндпоинт для отслеживания прогресса обработки (для progress bar).
    """
    status = ocr_service.progress_status.get(file_id)
    if not status:
        # Проверяем, может обработка уже завершена
        db_transcript = crud_transcripts.get_transcript_by_file_id(db, file_id)
        if db_transcript:
            return {"status": "completed", "progress": 100}
        # Если нет транскрипта, возможно, обработка еще не началась или произошла ошибка
        return {"status": "not_found", "progress": 0}
    return status

@router.post("/correction/{file_id}")
def submit_correction(file_id: uuid.UUID, correction: CorrectionData, db: Session = Depends(get_db)):
    """
    9) Принимает исправления от пользователя для последующего дообучения модели.
    """
    db_file = crud_files.get_file(db, file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="Файл не найден")

    crud_corrections.create_correction(db=db, file_id=file_id, correction=correction)
    
    return {"message": "Спасибо! Ваши исправления помогут нам улучшить модель."}

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    11) Возвращает статистику по обработанным документам.
    """
    total_count = crud_transcripts.get_total_processed_count(db)
    return {
        "processed_total": total_count
    }

@router.get("/{file_id}/upload")
def get_uploaded_file(file_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Возвращает загруженный файл.
    """
    db_file = crud_files.get_file(db, file_id)
    if not db_file or not os.path.exists(db_file.file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(db_file.file_path)

@router.get("/{file_id}/transcript")
def get_transcript_file(file_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Возвращает файл с результатами распознавания.
    """
    db_transcript = crud_transcripts.get_transcript_by_file_id(db, file_id)
    if not db_transcript or not os.path.exists(db_transcript.transcript_path):
        raise HTTPException(status_code=404, detail="Файл с транскрипцией не найден")
    return FileResponse(db_transcript.transcript_path)

@router.get("/", response_model=List[FileInDB])
def get_all_files(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """
    Возвращает список всех загруженных файлов.
    """
    files = crud_files.get_files(db, skip=skip, limit=limit)
    return files

@router.get("/transcripts", response_model=List[TranscriptInDB])
def get_all_transcripts(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """
    Возвращает список всех транскрипций.
    """
    transcripts = crud_transcripts.get_transcripts(db, skip=skip, limit=limit)
    return transcripts

