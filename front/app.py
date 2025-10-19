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
    return "http://127.0.0.1:8000/api/v1"

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

# Reusable CSS components
def load_custom_css():
    css = """
    <style>
    /* Import elegant fonts */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Lora:wght@400;500;600&family=Source+Sans+Pro:wght@300;400;600&display=swap');
    
    /* Main color palette - Archival beige/brown tones */
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
    
    /* Global styling */
    .stApp {
        background: linear-gradient(135deg, #FAF6F0 0%, #F5EFE6 100%);
    }
    /* FULLSCREEN HERO */
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
    
    /* Custom header with ornamental design */
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
    
    /* Decorative divider */
    .ornamental-divider {
        text-align: center;
        margin: 2rem 0;
        color: var(--accent-gold);
        font-size: 2rem;
    }
    
    /* Feature cards */
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
    }
    
    /* Upload section */
    .upload-zone {
        background: var(--light-parchment);
        border: 3px dashed var(--secondary-brown);
        border-radius: 20px;
        padding: 3rem;
        text-align: center;
        margin: 2rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-zone:hover {
        border-color: var(--accent-gold);
        background: var(--warm-cream);
        box-shadow: 0 8px 24px rgba(212, 175, 55, 0.2);
    }
     /* Центрируем и ограничиваем ширину самого uploader */
    [data-testid="stFileUploader"] { max-width: 820px; width: 100%; margin: 0 auto; }

    /* Делаем dropzone пунктирным прямоугольником (вся область — активная зона dnd) */
    [data-testid="stFileUploaderDropzone"] {
        border: 3px dashed #8B7355 !important;
        background: var(--light-parchment) !important;
        border-radius: 20px !important;
        min-height: 260px;
        display: flex; justify-content: center; align-items: center;
        padding: 24px;
    }
    /* Внутреннее выравнивание контента dropzone */
    [data-testid="stFileUploaderDropzone"] > div {
        display: flex; flex-direction: column; align-items: center; gap: 12px;
    }

    /* Кастомный текст/иконка подсказки */
    [data-testid="stFileUploaderDropzoneInstructions"] span { display: none !important; }
    [data-testid="stFileUploaderDropzoneInstructions"] > div::before {
        content: "☁️"; font-size: 42px; color: #8B7355; display: block; text-align: center; margin-bottom: 6px;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] > div::after {
        content: "Перетащите файл сюда или нажмите для выбора";
        color: #5C4033; font-size: 16px; opacity: 0.9; display: block; text-align: center;
    }

    /* Кнопка внутри прямоугольника */
    [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"],
    [data-testid="stFileUploaderDropzone"] [data-testid="stbaseButton-secondary"] {
        background-color: #8B7355 !important; color: #fff !important;
        border: none !important; border-radius: 10px !important; padding: 10px 18px !important;
    }
    [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stFileUploaderDropzone"] [data-testid="stbaseButton-secondary"]:hover {
        background-color: #7A654B !important;
    }
    /* Custom buttons - светлые кнопки */
    .stButton>button {
        background: linear-gradient(135deg, var(--secondary-brown) 0%, var(--deep-sepia) 100%);
        color: var(--warm-cream) !important;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 2.5rem;
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(92, 64, 51, 0.3);
    }

    /* Убедитесь, что все текстовые элементы внутри кнопки светлые */
    .stButton>button * {
        color: var(--warm-cream) !important;
        -webkit-text-fill-color: var(--warm-cream) !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--light-parchment) 0%, var(--primary-beige) 100%);
        border-right: 3px solid var(--border-vintage);
    }
    
    [data-testid="stSidebar"] .sidebar-content {
        padding: 2rem 1rem;
    }
    
    /* Info boxes */
    .info-box {
        background: rgba(212, 175, 55, 0.1);
        border-left: 5px solid var(--accent-gold);
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
        font-family: 'Source Sans Pro', sans-serif;
    }
    
    .success-box {
        background: rgba(139, 195, 74, 0.1);
        border-left: 5px solid #8BC34A;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
    }
    
    /* Progress indicators */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--accent-gold), var(--secondary-brown));
    }
    
    /* Document preview */
    .document-preview {
        border: 2px solid var(--border-vintage);
        border-radius: 10px;
        padding: 1rem;
        background: white;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, var(--warm-cream) 0%, var(--light-parchment) 100%);
        border: 2px solid var(--accent-gold);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
    }
    
    .stat-number {
        font-family: 'Playfair Display', serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--deep-sepia);
        display: block;
    }
    
    .stat-label {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 1rem;
        color: var(--secondary-brown);
        margin-top: 0.5rem;
    }
    
    /* Text styling */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif;
        color: var(--dark-brown);
    }
    
    p, li, span {
        font-family: 'Source Sans Pro', sans-serif;
        color: var(--deep-sepia);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: var(--light-parchment);
        border: 1px solid var(--border-vintage);
        border-radius: 8px;
        font-family: 'Lora', serif;
        color: var(--dark-brown);
    }
    
    /* File uploader styling */
    [data-testid="stFileUploader"] {
        background: var(--warm-cream);
        border: 2px solid var(--border-vintage);
        border-radius: 12px;
        padding: 2rem;
    }
    
    /* Selectbox and input styling */
    .stSelectbox, .stTextInput {
        font-family: 'Source Sans Pro', sans-serif;
    }
    
    /* Table styling */
    .dataframe {
        border: 2px solid var(--border-vintage);
        border-radius: 8px;
        font-family: 'Source Sans Pro', sans-serif;
    }
    
    /* Footer */
    .archive-footer {
        text-align: center;
        padding: 2rem;
        margin-top: 3rem;
        border-top: 2px solid var(--border-vintage);
        font-family: 'Source Sans Pro', sans-serif;
        color: var(--secondary-brown);
        font-size: 0.9rem;
    }
    
    /* Animation for document processing */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Tooltip styling */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
        color: var(--accent-gold);
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_header():
    st.markdown("""
    <div class="hero-fullscreen fade-in">
        <div class="hero-icon">📜</div>
        <div class="hero-title">Archive Vision</div>
        <div class="hero-subtitle">Автоматизированная система распознавания документов</div>
        <div class="hero-tagline">Сохраняем историю с помощью искусственного интеллекта</div>
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
            "title": "Распознавание ИИ",
            "description": "Современные алгоритмы машинного обучения, обученные на исторических документах. Высокая точность обработки рукописных и печатных архивных данных.",
            "col": col1
        },
        {
            "icon": "📊",
            "title": "Умная индексация",
            "description": "Автоматическое выделение ключевых данных и структурирование метаданных. Поиск по базе для генеалогии и исследований.",
            "col": col2
        },
        {
            "icon": "🗄️",
            "title": "Интеграция с базой",
            "description": "Подключение к архивным информационным системам. Формирование долгосрочной базы для хранения и поиска исторических данных.",
            "col": col3
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
        "<h2 style='text-align: center; font-family: Playfair Display, serif; color: #5C4033; margin-bottom: 1.5rem;'>📤 Загрузка Архивных Документов</h2>",
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
        
        st.info(f"📄 Обработка: **{file_name}**")
        
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
            status_text.text(f"Прогресс: {progress:.1f}%")
            
            if wait_result.get("completed"):
                # 4. Get final result
                result = get_transcript(file_id)
                if result["success"]:
                    transcript_data = result["data"]
                    st.session_state.processed_files[file_name] = {
                        "text": transcript_data.get("text", ""),
                        "path": temp_path,
                        "file_id": file_id,
                        "transcript_id": transcript_data.get("transcript_id")
                    }
                    st.success(f"✅ {file_name} обработан!")
                else:
                    st.error(f"❌ Не удалось получить результат для {file_name}")
                break
            
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

def render_footer():
    """Render elegant footer"""
    st.markdown("""
    <div class="archive-footer fade-in">
        <div style="font-family: Playfair Display, serif; font-size: 1.1rem; color: #5C4033; margin-bottom: 1rem;">
            ◈ ◆ ◈
        </div>
        <p style="margin: 0.5rem 0;">
            <strong>Moscow Main Archive Department</strong><br>
            Preserving the history of Moscow and its residents since 1962
        </p>
        <p style="margin: 1rem 0; font-size: 0.9rem;">
            Robotized Archive Cluster | Digital Preservation | Genealogical Research
        </p>
        <p style="margin: 0.5rem 0; font-size: 0.85rem; color: #8B7355;">
            © 2025 Moscow Archives. All historical documents are protected under Russian Federation law.
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_accuracy_card():
    """Display accuracy card with real backend data"""
    total_count = get_all_files_count()
    
    st.markdown(f"""
    <div class='stat-card fade-in' style='margin-top: 2rem;'>
        <div style='font-family: Playfair Display, serif; font-size: 2rem; color: #5C4033; letter-spacing: 2px;'>🎯 Точность Модели</div>
        <div style='font-family: Source Sans Pro, sans-serif; font-size:1.2rem; color:#704214; margin-top:1rem;'>
            Наш искусственный интеллект успешно распознал <strong>94,2%</strong> полей в архивных документах за последний месяц.
            <br>Оценка на основе <strong>{total_count:,}</strong> реальных документов периода 1772-1917 гг.<br>
            <span style='color: #8BC34A; font-weight: 600;'>Достоверность результатов подтверждена экспертами архива.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# Main application
def main():
    """Main application entry point"""
    load_custom_css()
    render_header()
    render_accuracy_card()
    render_features()
    render_upload_section()
    render_results_section()
    render_export_section()
    render_footer()

if __name__ == "__main__":
    main()