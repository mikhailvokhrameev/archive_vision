# /api/v1/endpoints/documents.py
import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from core.database import get_db
from core.config import settings
from crud import crud_files, crud_transcripts, crud_corrections
from schemas.document import FileCreate, FileInDB, CorrectionData
from services import ocr_service

router = APIRouter()

# Счетчик обработанных отчетов за сеанс (в памяти)
session_processed_count = 0

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
    
    # Создаем директорию для загрузок, если её нет
    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)

    for file in files:
        extension = file.filename.split('.')[-1].lower()
        if extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Файлы с расширением {extension} не поддерживаются.")
        
        # Генерируем уникальное имя файла
        unique_filename = f"{uuid.uuid4()}.{extension}"
        file_path = os.path.join(settings.UPLOAD_DIRECTORY, unique_filename)
        
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
    global session_processed_count
    
    transcript_path, wer = ocr_service.process_document_mock(file_id, file_path)
    crud_transcripts.create_file_transcript(db, file_id, transcript_path, wer)
    
    # 11) Инкремент счетчика
    session_processed_count += 1
    print(f"Отчеты за сессию: {session_processed_count}, Всего: {crud_transcripts.get_total_processed_count(db)}")

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
        # Здесь в реальном приложении была бы проверка в БД
        return {"status": "completed", "progress": 100}
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
        "processed_this_session": session_processed_count,
        "processed_total": total_count
    }
