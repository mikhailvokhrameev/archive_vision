"""
Moscow Archives Document Recognition System
A premium web interface for automated document processing and indexing
"""

import streamlit as st
import requests
import os
import json
from pathlib import Path
import time
from datetime import datetime
from PIL import Image
from io import BytesIO

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
    return "http://127.0.0.1:8001/api/v1"

API_BASE = get_api_base_url()
TEMP_DIR = "temp_uploads"

# Initialize temp directory
os.makedirs(TEMP_DIR, exist_ok=True)

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


# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Moscow Archives | Document Recognition",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Variables and Base Styles
CSS_VARIABLES = {
    'primary-beige': '#F5EFE6',
    'secondary-brown': '#8B7355', 
    'accent-gold': '#D4AF37',
    'dark-brown': '#5C4033',
    'light-parchment': '#FAF6F0',
    'deep-sepia': '#704214',
    'warm-cream': '#FFF8E7',
    'border-vintage': 'rgba(139, 115, 85, 0.3)'
}
def load_custom_css():
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Lora:wght@400;500;600&family=Source+Sans+Pro:wght@300;400;600&display=swap');
    
    :root {
        --primary-beige: #F5EFE6;
        --secondary-brown: #8B7355;
        --accent-gold: #D4AF37;
        --dark-brown: #5C4033;
        --light-parchment: #FAF6F0;
        --deep-sepia: #704214;
        --warm-cream: #FFF8E7;
        --border-vintage: rgba(139, 115, 85, 0.3);
    }
    
    .stApp {
        background: linear-gradient(135deg, #FAF6F0 0%, #F5EFE6 100%);
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }
    
    h1, h2, h3 {
        font-family: 'Playfair Display', serif;
        color: var(--dark-brown);
    }
    
    p, li, span {
        font-family: 'Source Sans Pro', sans-serif;
        color: var(--deep-sepia);
    }

    .hero-fullscreen {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 2rem;
    }

    .hero-icon {
        font-size: 5rem;
        margin-bottom: 1.5rem;
    }

    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 4.5rem;
        font-weight: 700;
        color: var(--dark-brown);
        letter-spacing: 3px;
    }

    .hero-subtitle {
        font-family: 'Lora', serif;
        font-size: 1.8rem;
        color: var(--secondary-brown);
        font-style: italic;
        margin-top: 1rem;
    }

    .hero-tagline {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 1.2rem;
        color: var(--deep-sepia);
        margin-top: 1rem;
    }

    .hero-divider {
        color: var(--accent-gold);
        font-size: 2.5rem;
        margin: 2rem 0;
    }
    
    .archive-header {
        text-align: center;
        padding: 3rem 2rem 2rem 2rem;
        background: linear-gradient(180deg, rgba(212, 175, 55, 0.15) 0%, rgba(245, 239, 230, 0.8) 100%);
        border-bottom: 3px double var(--secondary-brown);
        margin-bottom: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(92, 64, 51, 0.1);
    }
    
    .archive-title {
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem;
        font-weight: 700;
        color: var(--dark-brown);
        margin-bottom: 0.5rem;
        letter-spacing: 2px;
        text-shadow: 2px 2px 4px rgba(139, 115, 85, 0.2);
    }
    
    .archive-subtitle {
        font-family: 'Lora', serif;
        font-size: 1.3rem;
        color: var(--secondary-brown);
        font-style: italic;
        margin-top: 0.5rem;
    }
    
    .archive-tagline {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 1rem;
        color: var(--deep-sepia);
        margin-top: 1rem;
        opacity: 0.8;
    }
    
    .ornamental-divider {
        text-align: center;
        margin: 2rem 0;
        color: var(--accent-gold);
        font-size: 2rem;
    }
    
    .feature-card {
        background: var(--warm-cream);
        border: 2px solid var(--border-vintage);
        border-radius: 15px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 24px rgba(92, 64, 51, 0.15);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        min-height: 320px;
        display: flex;
        flex-direction: column;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--accent-gold), var(--secondary-brown));
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 32px rgba(92, 64, 51, 0.25);
        border-color: var(--accent-gold);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
    }

    .feature-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.8rem;
        color: var(--dark-brown);
        margin-bottom: 1rem;
        font-weight: 600;
    }

    .feature-description {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 1.05rem;
        color: var(--deep-sepia);
        line-height: 1.7;
        flex-grow: 1;
    }

    .stats-wrapper {
        margin: 32px 0;
    }

    .stats-hero {
        position: relative;
        padding: clamp(16px, 4vw, 48px);
        border-radius: 28px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        background: linear-gradient(135deg, var(--warm-cream) 0%, var(--light-parchment) 100%);
        color: var(--deep-sepia);
        border: 2px solid var(--accent-gold);
        box-shadow: 0 10px 28px rgba(92, 64, 51, 0.15);
    }

    .stats-number {
        font-family: 'Playfair Display', serif;
        font-weight: 700;
        font-size: clamp(32px, 7vw, 90px);
        line-height: 1;
        letter-spacing: 0.01em;
        font-variant-numeric: tabular-nums;
        color: var(--dark-brown);
    }

    .stats-caption {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: clamp(14px, 2vw, 22px);
        margin-top: clamp(6px, 1vw, 12px);
        color: var(--secondary-brown);
    }

    .stats-pill {
        position: absolute;
        top: clamp(10px, 2vw, 18px);
        right: clamp(10px, 2vw, 18px);
        border-radius: 999px;
        padding: 6px 14px;
        font-family: 'Source Sans Pro', sans-serif;
        font-size: clamp(12px, 1.6vw, 14px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.20);
        background: var(--warm-cream);
        color: var(--dark-brown);
        border: 1px solid var(--border-vintage);
    }
    
    [data-testid="stFileUploader"] {
        max-width: 820px;
        width: 100%;
        margin: 0 auto;
        background: var(--warm-cream);
        border: 2px solid var(--border-vintage);
        border-radius: 12px;
        padding: 2rem;
    }

    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] div {
        color: #5C4033 !important;
    }

    [data-testid="stFileUploaderFileName"] {
        color: #5C4033 !important;
        font-weight: 500 !important;
    }

    [data-testid="stFileUploaderFileSize"] {
        color: #8B7355 !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        border: 3px dashed #8B7355 !important;
        background: var(--light-parchment) !important;
        border-radius: 20px !important;
        min-height: 260px;
        display: flex; justify-content: center; align-items: center;
        padding: 24px;
    }
    
    [data-testid="stFileUploaderDropzone"] > div {
        display: flex; flex-direction: column; align-items: center; gap: 12px;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] span { display: none !important; }
    
    [data-testid="stFileUploaderDropzoneInstructions"] > div::before {
        content: "☁️";
        font-size: 42px;
        color: #8B7355;
        display: block;
        text-align: center;
        margin-bottom: 6px;
    }
    
    [data-testid="stFileUploaderDropzoneInstructions"] > div::after {
        content: "Перетащите файл сюда или нажмите для выбора";
        color: #5C4033;
        font-size: 16px;
        opacity: 0.9;
        display: block;
        text-align: center;
    }

    [data-testid="stFileUploaderDropzone"] [data-testid*="stBaseButton-secondary"] {
        background-color: #8B7355 !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 18px !important;
    }
    
    [data-testid="stFileUploaderDropzone"] [data-testid*="stBaseButton-secondary"]:hover {
        background-color: #7A654B !important;
    }
    
    .stButton > button,
    [data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg, var(--secondary-brown) 0%, var(--deep-sepia) 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-family: 'Source Sans Pro', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 12px rgba(92, 64, 51, 0.3) !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover,
    [data-testid="stDownloadButton"] > button:hover {
        background: linear-gradient(135deg, var(--deep-sepia) 0%, var(--dark-brown) 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(92, 64, 51, 0.4) !important;
    }

    .stButton > button *,
    [data-testid="stDownloadButton"] > button * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--light-parchment) 0%, var(--primary-beige) 100%);
        border-right: 3px solid var(--border-vintage);
    }
    
    .info-box {
        background: rgba(212, 175, 55, 0.1);
        border-left: 5px solid var(--accent-gold);
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
        font-family: 'Source Sans Pro', sans-serif;
    }

    .info-box * {
        color: #5C4033 !important;
    }
    
    .success-box {
        background: rgba(139, 195, 74, 0.1);
        border-left: 5px solid #8BC34A;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
    }
    
    .document-preview {
        border: 2px solid var(--border-vintage);
        border-radius: 10px;
        padding: 1rem;
        background: white;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        color: #5C4033 !important;
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--accent-gold), var(--secondary-brown));
    }
    
    .dataframe {
        border: 2px solid var(--border-vintage);
        border-radius: 8px;
        font-family: 'Source Sans Pro', sans-serif;
    }
    
    .archive-footer {
        text-align: center;
        padding: 1rem;
        margin-top: auto;
        border-top: 2px solid var(--border-vintage);
        font-family: 'Source Sans Pro', sans-serif;
        color: var(--secondary-brown);
        font-size: 0.9rem;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
        color: var(--accent-gold);
    }

    .streamlit-expanderHeader {
        background: var(--light-parchment) !important;
        border: 1px solid var(--border-vintage) !important;
        border-radius: 8px !important;
        font-family: 'Lora', serif !important;
        color: var(--dark-brown) !important;
    }

    .streamlit-expanderContent {
        background: var(--warm-cream) !important;
        border: 1px solid var(--border-vintage) !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        padding: 1.5rem !important;
    }

    .streamlit-expanderContent * {
        color: var(--dark-brown) !important;
    }

    [data-testid="stTextInput"] input {
        background-color: var(--warm-cream) !important;
        color: var(--dark-brown) !important;
        border: 2px solid var(--border-vintage) !important;
        border-radius: 8px !important;
    }

    [data-testid="stTextInput"] input::placeholder {
        color: var(--secondary-brown) !important;
        opacity: 0.7 !important;
    }

    [data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: var(--warm-cream) !important;
        color: var(--dark-brown) !important;
        border: 2px solid var(--border-vintage) !important;
    }

    div[data-testid="stVerticalBlock"] > div {
        background: transparent !important;
    }
    </style>
    """
    import streamlit as st
    st.markdown(css, unsafe_allow_html=True)





def render_header():
    st.markdown("""
    <div class="hero-fullscreen fade-in">
        <div class="hero-icon">📜</div>
        <div class="hero-title">Archive Vision</div>
        <div class="hero-subtitle">Автоматизированная система распознавания документов</div>
        <div class="hero-tagline">проект команды <b>bestbmstu</b></div>
        <div class="hero-divider">◈ ◆ ◈</div>
    </div>
    """, unsafe_allow_html=True)


def render_stats():
    """Render statistics cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    stats = [
        ("2,847", "Documents Processed", col1),
        ("94.2%", "Accuracy Rate", col2),
        ("1772-1917", "Time Period", col3),
        ("12", "Languages Supported", col4)
    ]
    
    for number, label, col in stats:
        with col:
            st.markdown(f"""
            <div class="stat-card fade-in">
                <span class="stat-number">{number}</span>
                <span class="stat-label">{label}</span>
            </div>
            """, unsafe_allow_html=True)

def render_features():
    st.markdown("<div class='ornamental-divider'>◈ ◆ ◈</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    features = [
        {
            "icon": "🔍",
            "title": "Современный подход к OCR",
            "description": """Используем модель TrOCR, дообученную на 73830 сегментах рукописных текстов на русском языке
                <br><br><strong>Преимущества:</strong>
                <br>• Открытый исходный код
                <br>• Возможность запуска в закрытом контуре""",
            "col": col1
        },
        {
            "icon": "✏️",
            "title": "Коррекция текста",
            "description": "Для дальнейшего улучшения работы сервиса эксперты имеют возможность корректировать результат распознавания",
            "col": col3
        },
        {
            "icon": "📚",
            "title": "История расшифровок",
            "description": "Эксперту доступна история всех когда-либо расшифрованных документов с возможностью экспорта расшифрованного текста в форматах json, csv и txt",
            "col": col2
        }
    ]
    for feature in features:
        with feature["col"]:
            st.markdown(f"""
            <div class="feature-card fade-in">
                <span class="feature-icon">{feature["icon"]}</span>
                <div class="feature-title">{feature["title"]}</div>
                <div class="feature-description">{feature["description"]}</div>
            </div>
            """, unsafe_allow_html=True)



def render_upload_section():
    """Upload section with backend integration"""
    st.markdown("<div class='ornamental-divider'>◈ ◆ ◈</div>", unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align: center; font-family: Playfair Display, serif; color: #5C4033; margin-bottom: 1.5rem;'>Загрузка Архивных Документов</h2>",
        unsafe_allow_html=True
    )

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        uploaded_files = st.file_uploader(
            label="",
            type=['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'tif'],
            accept_multiple_files=True,
            label_visibility="collapsed",
            help="Перетащите файлы или нажмите для выбора. Поддерживаются PDF, JPG, PNG, TIFF"
        )

        if uploaded_files:
            st.markdown(f"""
            <div class="info-box fade-in" style="color: #8B7355">
              <strong>📄 Загружено файлов: {len(uploaded_files)}</strong><br>
              Общий размер: <strong>{sum(f.size for f in uploaded_files) / (1024*1024):.2f} МБ</strong>
            </div>
            """, unsafe_allow_html=True)

            # Preview first image
            for uf in uploaded_files:
                if uf.type.startswith("image"):
                    st.markdown("<div class='document-preview fade-in'>", unsafe_allow_html=True)
                    st.image(uf, caption=f"Предпросмотр: {uf.name}", use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    break

            # Process button
            if st.button("🚀 Расшифровать Документы", use_container_width=True, key="process_btn"):
                process_documents_batch(uploaded_files)
                
def process_documents_batch(uploaded_files):
    """Process multiple documents with backend"""
    st.markdown("<div class='ornamental-divider'>◈ ◆ ◈</div>", unsafe_allow_html=True)
    st.markdown(
        "<h3 style='text-align: center; color: #8B7355; font-family: Playfair Display, serif;'>⚙️ Расшифровка Документов</h3>",
        unsafe_allow_html=True
    )
    
    st.session_state.total_session_files = len(uploaded_files)
    st.session_state.processed_files = {}
    
    for i, uploaded_file in enumerate(uploaded_files):
        file_name = uploaded_file.name
        
        st.info(f"📄 Обработка: {file_name}")
        
        # 1. Upload file
        upload_result = upload_file_to_backend(uploaded_file)
        if not upload_result["success"]:
            st.error(f"❌ Ошибка загрузки {file_name}: {upload_result['error']}")
            continue
        
        file_id = upload_result["file_id"]
        temp_path = upload_result["temp_path"]
        
        # 2. Start transcription
        transcribe_result = transcribe_file(file_id)
        if not transcribe_result["success"]:
            st.error(f"❌ Ошибка запуска обработки {file_name}: {transcribe_result['error']}")
            continue
        
        # 3. Wait for completion with progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        while True:
            wait_result = wait_for_processing(file_id)
            
            if not wait_result["success"]:
                st.error(f"❌ Ошибка ожидания {file_name}: {wait_result['error']}")
                break
            
            progress = wait_result.get("progress", 0)
            progress_bar.progress(int(progress))
            
            # ✅ ДОБАВЛЕН ВЫВОД ПРОЦЕНТОВ
            status_text.markdown(
                f"<div style='text-align: center; font-family: Source Sans Pro, sans-serif; "
                f"font-size: 1.1rem; color: #8B7355; margin-top: 0.5rem;'>"
                f"⏳ Прогресс: <strong>{progress:.1f}%</strong></div>",
                unsafe_allow_html=True
            )
            
            if wait_result.get("completed"):
                # 4. Get final result
                result = get_transcript(file_id)
                if result["success"]:
                    transcript_data = result["data"]
                    
                    # ✅ ИСПРАВЛЕНИЕ: Собираем текст из recognized_words
                    recognized_words = transcript_data.get("recognized_words", [])
                    text = " ".join([word.get("text", "") for word in recognized_words])
                    
                    st.session_state.processed_files[file_name] = {
                        "text": text,  # ✅ Теперь содержит реальный распознанный текст
                        "path": temp_path,
                        "file_id": file_id,
                        "transcript_id": transcript_data.get("transcript_id"),
                        "raw_data": transcript_data  # Сохраняем полный ответ для отладки
                    }
                    st.success(f"✅ {file_name} обработан!")
                else:
                    st.error(f"❌ Не удалось получить результат для {file_name}")
                break
            
            time.sleep(2)
            
            time.sleep(2)
    
    st.session_state.total_processed_count = len(st.session_state.processed_files)
    
    # Success message
    st.balloons()
    st.markdown(f"""
    <div class="success-box fade-in">
        <h3 style="margin-top: 0; color: #558B2F;">✅ Обработка Завершена!</h3>
        <p style="color: #33691E; font-size: 1.1rem;">
            Загружено файлов: <strong>{st.session_state.total_session_files}</strong><br>
            Успешно обработано: <strong>{st.session_state.total_processed_count}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)



def display_results():
    """Display processing results in elegant format"""
    st.markdown("<div class='ornamental-divider'>◈ ◆ ◈</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #5C4033; font-family: Playfair Display, serif;'>📋 Расшифрованный Документ</h2>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="fade-in" style="background: white; padding: 2rem; border: 2px solid #D4AF37; border-radius: 10px; font-family: Lora, serif; line-height: 1.8; color: #5C4033;">
            <em>Тысяча восемьсот восемьдесят пятаго года марта пятнадцатаго дня в метрическую книгу 
            церкви Святаго Николая Чудотворца записано: родился младенецъ мужеска пола, названъ Иваномъ, 
            крещенъ священникомъ Василiемъ Петровымъ. Родители: дворянинъ Петръ Ивановичъ Соколовъ и 
            законная жена его Марiя Александровна, православные...</em>
        </div>
        """, unsafe_allow_html=True)
    
    # Action buttons with enhanced styling
    st.markdown('<div class="action-buttons">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("📥 Экспорт БД", use_container_width=True, key="export_db")
    with col2:
        st.button("📄 Загрузить отчет", use_container_width=True, key="download_report")
    with col3:
        st.button("🔄 Process Another", use_container_width=True, key="process_another")
    st.markdown('</div>', unsafe_allow_html=True)

def render_archive_page():
    """Display all previously processed documents"""
    st.markdown("<div class='ornamental-divider'>◈ ◆ ◈</div>", unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align: center; color: #5C4033; font-family: Playfair Display, serif;'>🗄️ Архив Расшифрованных Документов</h2>",
        unsafe_allow_html=True
    )
    
    # Получаем список транскриптов (metadata)
    with st.spinner("Загрузка архива..."):
        transcripts_result = get_all_transcripts()
    
    if not transcripts_result["success"]:
        st.error(f"❌ Ошибка загрузки: {transcripts_result['error']}")
        return
    
    transcripts_meta = transcripts_result["data"]
    
    if not transcripts_meta:
        st.info("📭 Архив пуст. Загрузите документы на главной странице.")
        return
    
    # Статистика
    st.markdown(f"""
    <div style='text-align: center; margin: 1.5rem 0;'>
        <span style='font-family: "Lora", serif; font-size: 1.1rem; color: #704214;'>
            Всего документов в архиве: <strong style='font-size: 1.3rem;'>{len(transcripts_meta)}</strong>
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='ornamental-divider'>◈ ◆ ◈</div>", unsafe_allow_html=True)
    
    # Поиск
    search_query = st.text_input("🔍 Поиск по тексту", placeholder="Введите ключевое слово...", key="archive_search")
    
    # Отображение документов
    for idx, meta in enumerate(transcripts_meta):
        file_id = meta.get("file_id")
        transcript_id = meta.get("transcript_id")
        created_at = meta.get("created_at", "N/A")
        wer = meta.get("wer", {}).get("wer", "N/A")
        
        # ✅ ПОЛУЧАЕМ ПОЛНЫЙ ТРАНСКРИПТ с текстом
        full_transcript_result = get_transcript(file_id)
        
        if not full_transcript_result["success"]:
            st.warning(f"⚠️ Не удалось загрузить транскрипт для {file_id}")
            continue
        
        full_data = full_transcript_result["data"]
        recognized_words = full_data.get("recognized_words", [])
        
        # Извлекаем текст
        if recognized_words:
            text = " ".join([w.get("text", "") for w in recognized_words if isinstance(w, dict)])
        else:
            text = ""
        
        # Фильтр по поиску
        if search_query and text and search_query.lower() not in text.lower():
            continue
        
        # Отображение
        with st.expander(f"📄 **Документ #{transcript_id[:8]}** — {created_at[:10]}"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown(f"""
                <div style='background: rgba(212, 175, 55, 0.1); border-left: 5px solid #D4AF37; 
                     padding: 1rem; border-radius: 8px; color: #5C4033;'>
                    <strong style='color: #5C4033;'>📋 Метаданные</strong><br><br>
                    <span style='color: #704214;'><strong>File ID:</strong> {file_id}</span><br>
                    <span style='color: #704214;'><strong>Transcript ID:</strong> {transcript_id}</span><br>
                    <span style='color: #704214;'><strong>Создан:</strong> {created_at[:19]}</span><br>
                    <span style='color: #704214;'><strong>Слов:</strong> {len(recognized_words)}</span><br>
                    <span style='color: #704214;'><strong>WER:</strong> {wer}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Скачивание
                st.download_button(
                    "📥 Скачать JSON",
                    data=json.dumps(full_data, ensure_ascii=False, indent=2),
                    file_name=f"transcript_{transcript_id[:8]}.json",
                    mime="application/json",
                    use_container_width=True,
                    key=f"download_{idx}_{transcript_id}"
                )
            
            with col2:
                st.markdown("<strong style='color: #5C4033;'>📝 Распознанный текст</strong>", unsafe_allow_html=True)
                
                if text:
                    st.markdown(f"""
                    <div style='height: 300px; overflow-y: auto; padding: 1.5rem; 
                         background: white; border: 2px solid #D4AF37; border-radius: 8px; 
                         color: #5C4033; font-family: Lora, serif; line-height: 1.8;'>
                        {text}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Текст не распознан")
                
                # Уверенность
                if recognized_words:
                    avg_conf = sum(w.get("confidence", 0) for w in recognized_words) / len(recognized_words)
                    st.progress(avg_conf, text=f"Средняя уверенность: {avg_conf*100:.1f}%")





def render_results_section():
    """Display and edit transcribed results"""
    if not st.session_state.processed_files:
        return
    
    st.markdown("<div class='ornamental-divider'>◈ ◆ ◈</div>", unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align: center; color: #5C4033; font-family: Playfair Display, serif;'>📋 Результаты Расшифровки</h2>",
        unsafe_allow_html=True
    )
    
    for file_name, data in st.session_state.processed_files.items():
        with st.expander(f"📄 **{file_name}** (File ID: {data['file_id']})"):
            col1, col2 = st.columns(2)
            
            # Preview image
            with col1:
                try:
                    if data["path"].lower().endswith('.pdf'):
                        st.info("📕 PDF файл (предпросмотр недоступен)")
                    else:
                        img = Image.open(data["path"])
                        st.image(img, caption="Оригинал документа", use_container_width=True)
                except Exception as e:
                    st.warning(f"⚠️ Не удалось загрузить изображение: {e}")
            
            # Editable text
            with col2:
                edited_text = st.text_area(
                    "Распознанный текст (редактируемый)",
                    value=data["text"],
                    height=300,
                    key=f"text_{file_name}"
                )
                
                # Auto-save changes
                if edited_text != data["text"]:
                    if update_transcript(data["transcript_id"], edited_text):
                        st.session_state.processed_files[file_name]["text"] = edited_text
                        st.success("💾 Изменения сохранены")
                    else:
                        st.error("❌ Не удалось сохранить изменения")


def render_export_section():
    """Export processed documents"""
    if not st.session_state.get("processed_files"):
        return

    # --- UI Elements ---
    st.markdown("<div class='ornamental-divider'>◈ ◆ ◈</div>", unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align: center; color: #5C4033; font-family: Playfair Display, serif;'>📥 Экспорт Данных</h2>",
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        export_format = st.selectbox(
            "Формат экспорта:",
            ("JSON", "CSV", "TXT"),
            key="export_format_selector"
        )
    
    with col2:
        if st.button("📦 Экспортировать данные", use_container_width=True):
            # Define a placeholder for the content to be downloaded.
            export_str = None
            
            # --- JSON Export Logic ---
            if export_format == "JSON":
                # IMPORTANT: Define the base URL for your FastAPI backend.
                # This might come from st.secrets or a config file.
                
                all_transcripts = {}
                try:
                    with st.spinner("Загрузка данных с сервера..."):
                        for name, data in st.session_state.processed_files.items():
                            file_id = data.get("file_id")
                            if file_id:
                                api_url = f"{API_BASE}/documents/export/json/{file_id}"
                                response = requests.get(api_url)
                                response.raise_for_status()  # Raise an exception for HTTP error codes
                                
                                # Use the original filename as the key in the combined JSON
                                all_transcripts[name] = response.json()
                    
                    export_str = json.dumps(all_transcripts, ensure_ascii=False, indent=4)
                    mime = "application/json"
                    file_ext = ".json"
                
                except requests.exceptions.RequestException as e:
                    st.error(f"Ошибка при экспорте JSON: Не удалось связаться с API. {e}")
                    st.stop() # Stop execution to prevent showing a broken download button

            # --- CSV/TXT Export Logic (Original logic) ---
            else:
                export_data_list = []
                for name, data in st.session_state.processed_files.items():
                    export_data_list.append({
                        "filename": name,
                        "file_id": data["file_id"],
                        "transcript_id": data["transcript_id"],
                        "text": data["text"]
                    })
                
                if export_format == "CSV":
                    csv_lines = ['"filename","file_id","transcript_id","text"']
                    for item in export_data_list:
                        text_escaped = item['text'].replace('"', '""')
                        csv_lines.append(
                            f'"{item["filename"]}","{item["file_id"]}","{item["transcript_id"]}","{text_escaped}"'
                        )
                    export_str = "\n".join(csv_lines)
                    mime = "text/csv"
                    file_ext = ".csv"
                
                else:  # TXT
                    txt_lines = []
                    for item in export_data_list:
                        txt_lines.append(f"{'='*60}\nФайл: {item['filename']}\nFile ID: {item['file_id']}\n{'='*60}\n{item['text']}\n")
                    export_str = "\n".join(txt_lines)
                    mime = "text/plain"
                    file_ext = ".txt"
            
            # --- Download Button ---
            # This button is rendered only if the 'export_str' was successfully created.
            if export_str:
                st.download_button(
                    label="💾 Скачать файл",
                    data=export_str,
                    file_name=f"archive_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}",
                    mime=mime,
                    use_container_width=True
                )

def render_accuracy_card():
    total_count = get_all_files_count()
    total_str = f"{total_count:,}".replace(",", " ")  # 20 436 091

    st.markdown(f"""
    <div class="stats-wrapper">
      <section class="stats-hero fade-in">
        <div class="stats-number">{total_str}</div>
        <div class="stats-caption">архивных документов расшифровано</div>
      </section>
    </div>
    """, unsafe_allow_html=True)



# Main application
def main():
    """Main application entry point"""
    load_custom_css()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <div style='font-size: 3rem;'>📜</div>
            <div style='font-family: Playfair Display, serif; font-size: 1.5rem; color: #5C4033;'>
                Archive Vision
            </div>
            <div style='color: #8B7355; margin-top: 0.5rem;'>
                Навигация
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # ✅ ИСПРАВЛЕНИЕ: Добавлен параметр key
        page = st.radio(
            "Выберите страницу:",
            ["🏠 Главная", "🗄️ Архив Документов"],
            label_visibility="collapsed",
            key="navigation_radio"  # ✅ Уникальный ключ
        )
    
    # Render selected page
    if page == "🏠 Главная":
        render_header()
        render_accuracy_card()
        render_features()
        render_upload_section()
        render_results_section()
        render_export_section()
    
    elif page == "🗄️ Архив Документов":
        render_archive_page()
    
    # render_footer()


if __name__ == "__main__":
    main()