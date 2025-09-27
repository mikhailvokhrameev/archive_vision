# main.py
import io
import json
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

# CORS
from fastapi.middleware.cors import CORSMiddleware

# Импортируем наши модули (заглушки выше)
from ocr import recognize_text_from_file
from utils import save_upload_file
from database import save_recognition, update_recognition, get_recognition, save_file_record

app = FastAPI(
    title="Modular Image to Text API",
    description="API для распознавания текста, разделенное на модули.",
    version="1.1.0"
)

# Разрешаем запросы с Streamlit (обычно localhost:8501)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost", "http://127.0.0.1",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextPayload(BaseModel):
    text: str
    filename: str = "extracted_text"

# Папка для сохранения загруженных файлов
UPLOAD_DIR = "./data/"

@app.post("/files/upload/", summary="Загрузить файл и сохранить запись в таблицу files (без OCR)")
async def upload_file_to_files_table(file: UploadFile = File(...)):
    try:
        filepath = save_upload_file(file, UPLOAD_DIR)
        ext = Path(file.filename).suffix.lstrip(".")
        if not ext:
            raise HTTPException(status_code=400, detail="Не удалось определить расширение файла.")
        ext = ext.lower()
        saved = save_file_record(filepath, file.filename, ext)
        if saved is None:
            raise HTTPException(status_code=500, detail="Не удалось сохранить запись файла в БД.")
        return JSONResponse(
            content={
                "file_id": saved["file_id"],
                "file_name": file.filename,
                "file_extension": ext,
                "file_path": filepath,
                "load_date": saved["load_date"].isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Произошла ошибка: {e}")

@app.post("/recognize/", summary="Загрузить, распознать и сохранить")
async def recognize_endpoint(file: UploadFile = File(...)):
    try:
        filepath = save_upload_file(file, UPLOAD_DIR)
        extracted_text = recognize_text_from_file(filepath)
        record_id = save_recognition(file.filename, extracted_text)
        if record_id is None:
            raise HTTPException(status_code=500, detail="Не удалось сохранить результат в БД.")
        return JSONResponse(content={"record_id": record_id, "text": extracted_text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Произошла ошибка: {e}")

@app.post("/download/txt/", summary="Скачать текст в формате .txt")
async def download_as_txt(payload: TextPayload):
    file_like = io.BytesIO(payload.text.encode("utf-8"))
    filename = f"{payload.filename}.txt"
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return StreamingResponse(file_like, media_type="text/plain", headers=headers)

@app.post("/download/json/", summary="Скачать текст в формате .json")
async def download_as_json(payload: TextPayload):
    json_content = json.dumps({"source_filename": payload.filename, "text": payload.text}, ensure_ascii=False, indent=4)
    file_like = io.BytesIO(json_content.encode("utf-8"))
    filename = f"{payload.filename}.json"
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return StreamingResponse(file_like, media_type="application/json", headers=headers)

@app.put("/recognitions/{record_id}", summary="Обновить распознанный текст")
async def update_text_endpoint(record_id: int, payload: TextPayload):
    success = update_recognition(record_id, payload.text)
    if not success:
        raise HTTPException(status_code=404, detail="Запись с таким ID не найдена или не удалось обновить.")
    return {"message": "Текст успешно обновлен"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
