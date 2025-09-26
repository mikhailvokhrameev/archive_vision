import io
import json
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

from ocr import recognize_text_from_file
from utils import save_upload_file
from database import save_recognition, update_recognition, get_recognition, save_file_record


app = FastAPI(
    title="Modular Image to Text API",
    description="API для распознавания текста, разделенное на модули.",
    version="1.1.0"
)

class TextPayload(BaseModel):
    text: str
    filename: str = "extracted_text"

# Изменить на нужный путь!
UPLOAD_DIR = "./data/" 

# --- Эндпоинты API ---

@app.post("/files/upload/", summary="Загрузить файл и сохранить запись в таблицу files (без OCR)")
async def upload_file_to_files_table(file: UploadFile = File(...)):
    """
    Сохраняет файл на диск и добавляет запись в таблицу files.
    Возвращает file_id и метаданные.
    """
    try:
        # 1) Сохранить файл на диск (utils.save_upload_file должен возвращать полный путь)
        filepath = save_upload_file(file, UPLOAD_DIR)

        # 2) Извлечь расширение (без точки), привести к нижнему регистру
        ext = Path(file.filename).suffix.lstrip(".")
        if not ext:
            raise HTTPException(status_code=400, detail="Не удалось определить расширение файла.")
        ext = ext.lower()

        # 3) Сохранить метаданные в таблицу files
        saved = save_file_record(filepath, file.filename, ext)
        if saved is None:
            raise HTTPException(status_code=500, detail="Не удалось сохранить запись файла в БД.")
        
        # 4) Вернуть успешный ответ
        return JSONResponse(
            content={
                "file_id": saved["file_id"],
                "file_name": file.filename,
                "file_extension": ext,
                "file_path": filepath,
                "load_date": saved["load_date"].isoformat() if saved.get("load_date") else None
            }
        )
    except ValueError as e:
        # Ошибка валидации расширения
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Произошла ошибка: {e}")

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



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)