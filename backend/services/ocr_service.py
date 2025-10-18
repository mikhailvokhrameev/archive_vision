# /services/ocr_service.py
import time
import random
import json
import os
from schemas.document import RecognitionResult, TranscriptData
from core.config import settings
import uuid

# Временное хранилище для статуса прогресса
# В реальном проекте здесь будет Celery/Redis
progress_status = {}

def process_document_mock(file_id: uuid.UUID, file_path: str):
    """
    Имитация процесса нормализации и распознавания.
    """
    print(f"Начало обработки файла: {file_path}")
    
    # 1. Имитация нормализации изображения
    for i in range(1, 11):
        time.sleep(0.2)
        progress_status[file_id] = {"status": "normalizing", "progress": i * 10}
        print(f"Нормализация... {i*10}%")
    
    # 2. Имитация OCR
    for i in range(1, 11):
        time.sleep(0.3)
        progress_status[file_id] = {"status": "recognizing", "progress": i * 10}
        print(f"Распознавание... {i*10}%")
        
    # 3. Генерация mock-результата
    words = ["Пример", "распознанного", "текста", "с", "низкой", "уверенностью"]
    recognized_words = []
    for i, word in enumerate(words):
        recognized_words.append(
            TranscriptData(
                text=word,
                coordinates=[10 + i*80, 20, 80 + i*80, 50],
                # Случайно делаем одно слово неуверенным
                confidence=0.005 if word == "низкой" else round(random.uniform(0.8, 1.0), 3)
            )
        )
    
    result = RecognitionResult(
        wer=round(random.uniform(0.05, 0.25), 2),
        recognized_words=recognized_words,
        extracted_attributes={
            "ФИО": "Петров Петр Петрович",
            "дата_рождения": "12.05.1985",
            "адрес": "г. Москва, ул. Ленина, д. 1",
            "архивный_номер": "Ф-123, Оп-4, Д-56"
        }
    )

    # Сохраняем результат в JSON файл
    transcript_filename = f"{file_id}_transcript.json"
    transcript_path = os.path.join(settings.UPLOAD_DIRECTORY, transcript_filename)
    
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(result.model_dump_json(indent=4))
        
    print(f"Обработка файла {file_path} завершена. Результат сохранен в {transcript_path}")
    del progress_status[file_id] # Очищаем статус после завершения
    
    return transcript_path, result.wer
