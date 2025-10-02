import os
import shutil
from fastapi import UploadFile

def save_upload_file(upload_file: UploadFile, destination_folder: str) -> str:
    try:
        os.makedirs(destination_folder, exist_ok=True)
        
        filepath = os.path.join(destination_folder, upload_file.filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            
        return filepath
    finally:
        upload_file.file.close()
