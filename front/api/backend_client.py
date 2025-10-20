import requests
import os
import streamlit as st
import time
# --- Backend Configuration ---
def get_api_base_url():
    """Get API base URL from environment, secrets, or default"""
    # 1. Check for Docker/CI environment variable
    env_url = os.environ.get("API_BASE_URL")
    if env_url:
        return env_url
    # 2. Check for Streamlit secrets (for deployment)
    try:
        api_url = st.secrets.get("API_BASE_URL")
        if api_url:
            return api_url
    except Exception:
        pass
    # 3. Fallback for local development
    return "http://127.0.0.1:8000/api/v1"

API_BASE = get_api_base_url()

def process_file(file_id):
    """Start processing uploaded file"""
    try:
        response = requests.post(
            f"{API_BASE}/documents/{file_id}/process",
            timeout=600  # 10 минут на обработку
        )
        
        if response.status_code == 202:
            return {"success": True, "message": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Session State Initialization ---
def initialize_session_state():
    """Initialize session state variables"""
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = {}
    if "total_session_files" not in st.session_state:
        st.session_state.total_session_files = 0
    if "total_processed_count" not in st.session_state:
        st.session_state.total_processed_count = 0
    if "current_file_id" not in st.session_state:
        st.session_state.current_file_id = None

initialize_session_state()



# --- Backend API Functions ---
def upload_file_to_backend(uploaded_file):
    """Upload file to backend and return file_id"""
    try:
        # Сохраняем файл временно
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # Загружаем на бэкенд
        with open(temp_path, "rb") as f:
            files = [("files", (uploaded_file.name, f, uploaded_file.type))]
            response = requests.post(
                f"{API_BASE}/documents/upload",
                files=files,
                timeout=300
            )
        
        if response.status_code == 201:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                file_id = data[0]["file_id"]
                return {
                    "success": True, 
                    "file_id": file_id,
                    "temp_path": temp_path  # ← Добавьте эту строку
                }
            else:
                return {"success": False, "error": "Пустой ответ"}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def transcribe_file(file_id):
    """Start transcription for uploaded file"""
    try:
        response = requests.post(f"{API_BASE}/documents/{file_id}/process")
        if response.status_code == 202:
            # 202 = обработка запущена, но еще не завершена
            return {
                "success": True,
                "file_id": file_id,  # Сохраняем file_id для последующего опроса
                "message": "Обработка запущена"
            }
        else:
            return {
                "success": False,
                "error": f"Ошибка расшифровки: {response.status_code} - {response.text}"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def wait_for_processing(file_id, max_wait=600):
    """Wait for document processing to complete with progress tracking"""
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            # Проверяем статус
            response = requests.get(
                f"{API_BASE}/documents/process-status/{file_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                progress = data.get("progress", 0)
                
                # Возвращаем текущий прогресс
                if status == "completed":
                    return {"success": True, "completed": True, "progress": 100}
                elif status == "failed":
                    return {"success": False, "error": "Обработка не удалась"}
                else:
                    return {"success": True, "completed": False, "progress": progress}
            
            time.sleep(2)
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return {"success": False, "error": "Превышено время ожидания"}

def update_transcript(transcript_id, new_text):
    """Update transcript text"""
    try:
        response = requests.post(
            f"{API_BASE}/transcripts/{transcript_id}/edit",
            json={"text": new_text}
        )
        return response.status_code == 200
    except Exception:
        return False

def get_transcript(file_id):
    """Get processing results"""
    try:
        response = requests.get(
            f"{API_BASE}/documents/{file_id}/transcript",
            timeout=30
        )
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_all_files_count():
    """Get total count of processed files"""
    try:
        response = requests.get(f"{API_BASE}/documents/stats")
        if response.status_code == 200:
            count = response.json()
            return count["processed_total"]
        return 0
    except Exception:
        return 0

def get_all_transcripts():
    """Get all transcripts from backend"""
    try:
        response = requests.get(f"{API_BASE}/documents/transcripts", timeout=30)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_all_files():
    """Get all uploaded files from backend"""
    try:
        response = requests.get(f"{API_BASE}/documents/", timeout=30)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_file_by_id(file_id):
    """Get specific file info"""
    try:
        response = requests.get(f"{API_BASE}/documents/{file_id}/upload", timeout=30)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_corrections(file_id, corrections):
    """Save corrected text fragments to the backend."""
    try:
        response = requests.post(
            f"{API_BASE}/documents/{file_id}/corrections",
            json=corrections,
            timeout=60
        )
        if response.status_code == 201:
            return {"success": True, "message": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}