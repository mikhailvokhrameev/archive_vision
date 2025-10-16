import os
import re
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import json

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres123")
DB_HOST = os.getenv("DB_HOST", "postgres")  # Имя сервиса в Docker Compose
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "archive")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def wait_for_db():
    """Ждем пока база данных станет доступной"""
    for i in range(10):
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as connection:
                print("✅ Database connection established successfully.")
                return engine
        except Exception as e:
            print(f"⏳ Database not ready yet (attempt {i+1}/10): {e}")
            time.sleep(5)
    raise Exception("❌ Could not connect to database after 10 attempts")

# Используем функцию ожидания
try:
    engine = wait_for_db()
except Exception as e:
    print(f"Failed to connect to the database: {e}")
    engine = None

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        print("Database connection established successfully.")
except Exception as e:
    print(f"Failed to connect to the database: {e}")
    engine = None
    
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        print("Database connection established successfully.")
except Exception as e:
    print(f"Failed to connect to the database: {e}")
    engine = None

# === ДОБАВЬТЕ ЭТОТ КОД ===
def create_tables_if_not_exist():
    """Create necessary tables if they don't exist"""
    if not engine:
        print("Cannot create tables: database engine not available")
        return
    
    tables_creation_queries = [
        """
        CREATE TABLE IF NOT EXISTS files (
            file_id SERIAL PRIMARY KEY,
            file_path VARCHAR(500) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_extension VARCHAR(10) NOT NULL,
            load_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS file_transcripts (
            transcript_id SERIAL PRIMARY KEY,
            file_id INTEGER REFERENCES files(file_id),
            transcript_path VARCHAR(500),
            wer JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    
    try:
        with engine.connect() as connection:
            for query in tables_creation_queries:
                connection.execute(text(query))
            connection.commit()
        print("✅ Tables created/verified successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

# Вызовите функцию при импорте
create_tables_if_not_exist()

def execute_query(query, params=None):
    if not engine:
        raise ConnectionError("Database engine is not available.")
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            connection.commit()
            return result
    except SQLAlchemyError as e:
        print(f"Database query failed: {e}")
        return None

def get_all_files():
    query = "SELECT file_id, file_path, file_name, file_extension, load_date FROM files"
    result = execute_query(query)
    if result:
        return [dict(row._mapping) for row in result]
    return []


def save_file_record(file_path: str, file_name: str, file_extension: str) -> dict | None:
    if not re.match(r'^[a-zA-Z0-9]+$', file_extension):
        raise ValueError("Invalid file extension: only alphanumeric characters are allowed.")

    query = """
        INSERT INTO files (file_path, file_name, file_extension)
        VALUES (:file_path, :file_name, :file_extension)
        RETURNING file_id, load_date;
    """
    params = {
        "file_path": file_path,
        "file_name": file_name,
        "file_extension": file_extension
    }
    
    result = execute_query(query, params)
    if result:
        row = result.first()
        if row:
            return {"file_id": row.file_id, "load_date": row.load_date}
    return None

def get_file_record(file_id: int) -> dict | None:
    query = "SELECT file_id, file_path, file_name, file_extension, load_date FROM files WHERE file_id = :file_id;"
    result = execute_query(query, {"file_id": file_id})
    if result:
        row = result.first()
        if row:
            return dict(row._mapping)
    return None


def save_transcript_record(file_id: int, transcript_path: str, wer: dict) -> int | None:
    query = """
        INSERT INTO file_transcripts (file_id, transcript_path, wer)
        VALUES (:file_id, :transcript_path, :wer)
        RETURNING transcript_id;
    """
    # Convert dict to JSON string for the database
    wer_json = json.dumps(wer)
    
    params = {
        "file_id": file_id,
        "transcript_path": transcript_path,
        "wer": wer_json
    }

    result = execute_query(query, params)
    return result.scalar_one_or_none() if result else None

def get_transcript_record(transcript_id: int) -> dict | None:
    query = "SELECT transcript_id, file_id, transcript_path, wer FROM file_transcripts WHERE transcript_id = :transcript_id;"
    result = execute_query(query, {"transcript_id": transcript_id})
    if result:
        row = result.first()
        if row:
            return dict(row._mapping)
    return None

def get_transcripts_for_file(file_id: int) -> list[dict]:
    query = "SELECT transcript_id, transcript_path, wer, created_at FROM file_transcripts WHERE file_id = :file_id;"
    result = execute_query(query, {"file_id": file_id})
    return [dict(row._mapping) for row in result] if result else []
