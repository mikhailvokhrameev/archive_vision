import os
import shutil
from fastapi import UploadFile

def save_upload_file(upload_file: UploadFile, destination_folder: str) -> str:
    """
    Сохраняет загруженный файл в указанную папку и возвращает полный путь.
    """
    try:
        # Создаем папку, если она не существует
        os.makedirs(destination_folder, exist_ok=True)
        
        # Формируем путь к файлу
        filepath = os.path.join(destination_folder, upload_file.filename)
        
        # Сохраняем файл
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            
        return filepath
    finally:
        # Важно закрыть файл после всех операций
        upload_file.file.close()
