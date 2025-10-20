# /api/v1/endpoints/reports.py
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import io

router = APIRouter()

@router.post("/generate", response_class=StreamingResponse)
def generate_report(attributes: List[str]):
    """
    12) Конструктор отчетов. Генерирует и отдает файл для скачивания.
    В теле запроса ожидается JSON-массив с ID файлов и списком атрибутов.
    Пример тела: {"file_ids": [1, 2], "attributes": ["ФИО", "адрес"]}
    Для упрощения, мы просто выгрузим все атрибуты всех обработанных файлов.
    """
    # В реальном приложении здесь будет логика извлечения данных из БД по file_ids
    # Для примера, мы просто создадим отчет на лету
    
    output = io.StringIO()
    output.write(",".join(attributes) + "\n")
    
    # Mock-данные
    mock_data = [
        {"ФИО": "Петров П.П.", "дата_рождения": "12.05.1985", "адрес": "г. Москва"},
        {"ФИО": "Сидоров С.С.", "дата_рождения": "20.11.1970", "адрес": "г. Санкт-Петербург"}
    ]
    
    for item in mock_data:
        row = [item.get(attr, "N/A") for attr in attributes]
        output.write(",".join(row) + "\n")
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=report.csv"}
    )
