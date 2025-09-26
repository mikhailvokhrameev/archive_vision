# database.py
import re
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# !!! ВАЖНО: Замените на ваши реальные данные для подключения к БД !!!
DATABASE_URL = "postgresql://imoscow_admin:pudge@localhost:5432/imoscow_test"

try:
    engine = create_engine(DATABASE_URL)
    # Пробное подключение для проверки
    with engine.connect() as connection:
        print("Успешное подключение к базе данных!")
except Exception as e:
    print(f"Ошибка подключения к базе данных: {e}")
    engine = None

def execute_query(query, params=None):
    """Универсальная функция для выполнения запросов."""
    if not engine:
        raise ConnectionError("Не удалось подключиться к базе данных.")
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            connection.commit()
            return result
    except SQLAlchemyError as e:
        print(f"Ошибка выполнения запроса: {e}")
        return None

def save_recognition(filename: str, original_text: str) -> int | None:
    """Сохраняет результат распознавания в БД и возвращает ID записи."""
    query = "INSERT INTO recognitions (filename, text_content) VALUES (:filename, :text) RETURNING id;"
    result = execute_query(query, {"filename": filename, "text": original_text})
    return result.scalar_one_or_none() if result else None

def update_recognition(record_id: int, new_text: str) -> bool:
    """Обновляет текст для существующей записи в БД."""
    query = "UPDATE recognitions SET text_content = :text WHERE id = :id;"
    result = execute_query(query, {"id": record_id, "text": new_text})
    # rowcount > 0 означает, что строка была успешно обновлена
    return result.rowcount > 0 if result else False

def get_recognition(record_id: int) -> dict | None:
    """Получает запись из БД по ее ID."""
    query = "SELECT id, filename, text_content FROM recognitions WHERE id = :id;"
    result = execute_query(query, {"id": record_id})
    row = result.first() if result else None
    if row:
        return {"id": row.id, "filename": row.filename, "text": row.text_content}
    return None

def save_file_record(file_path: str, file_name: str, file_extension: str) -> dict | None:
    """
    Сохраняет запись о файле в таблицу files.
    Возвращает словарь {'file_id': int, 'load_date': datetime} или None при ошибке.
    Бросает ValueError, если расширение невалидно.
    """
    # Валидация расширения — совпадает с CHECK в схеме таблицы
    if not re.match(r"^[a-zA-Z0-9]+$", file_extension):
        raise ValueError("Invalid file_extension: only alphanumeric characters allowed")

    query = """
        INSERT INTO files (file_path, file_name, file_extension)
        VALUES (:file_path, :file_name, :file_extension)
        RETURNING file_id, load_date;
    """
    params = {"file_path": file_path, "file_name": file_name, "file_extension": file_extension}

    try:
        result = execute_query(query, params)
        if not result:
            return None
        row = result.first()
        if not row:
            return None
        return {"file_id": row.file_id, "load_date": row.load_date}
    except SQLAlchemyError as e:
        print(f"Ошибка при сохранении записи файла: {e}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка в save_file_record: {e}")
        return None
