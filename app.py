import io
import json
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from ocr import recognize_text_from_file
from utils import save_upload_file
from database import save_recognition, update_recognition, get_recognition 


app = FastAPI(
    title="Modular Image to Text API",
    description="API для распознавания текста, разделенное на модули.",
    version="1.1.0"
)

class TextPayload(BaseModel):
    text: str
    filename: str = "extracted_text"

UPLOAD_DIR = "uploads"

# --- Эндпоинты API ---

@app.post("/recognize/", summary="Загрузить, распознать и сохранить")
async def recognize_endpoint(file: UploadFile = File(...)):
    """
    Принимает файл, распознает текст и СОХРАНЯЕТ результат в БД.
    Возвращает ID новой записи и текст.
    """
    try:
        filepath = save_upload_file(file, UPLOAD_DIR)
        
        # Распознаем текст
        extracted_text = recognize_text_from_file(filepath)
        
        # Сохраняем в БД и получаем ID
        record_id = save_recognition(file.filename, extracted_text)
        
        if record_id is None:
            raise HTTPException(status_code=500, detail="Не удалось сохранить результат в БД.")

        return JSONResponse(
            content={"record_id": record_id, "text": extracted_text}
        )
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Произошла ошибка: {e}")


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
    """
    Принимает отредактированный текст и обновляет запись в БД по ID.
    """
    success = update_recognition(record_id, payload.text)
    if not success:
        raise HTTPException(status_code=404, detail="Запись с таким ID не найдена или не удалось обновить.")
    
    return {"message": "Текст успешно обновлен"}