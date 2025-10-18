"""
Moscow Archives Document Recognition System
A premium web interface for automated document processing and indexing
"""

import streamlit as st
import base64
from pathlib import Path
import time
from datetime import datetime

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Moscow Archives | Document Recognition",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium archival aesthetic
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
    
    /* Custom buttons */
    .stButton>button {
        background: linear-gradient(135deg, var(--secondary-brown) 0%, var(--deep-sepia) 100%);
        color: var(--warm-cream);
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
    
    .stButton>button:hover {
        background: linear-gradient(135deg, var(--deep-sepia) 0%, var(--dark-brown) 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(92, 64, 51, 0.4);
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
    <div class="archive-header fade-in">
        <div class="archive-title">📜 Архив Москвы</div>
        <div class="archive-subtitle">Автоматизированная система распознавания документов</div>
        <div class="archive-tagline">Сохраняем историю с помощью искусственного интеллекта</div>
        <div class="ornamental-divider">◈ ◆ ◈</div>
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
    """Render document upload interface"""
    st.markdown("<div class='ornamental-divider'>◈ ◆ ◈</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; font-family: Playfair Display, serif; color: #5C4033; margin-bottom: 2rem;'>📤 Upload Archival Documents</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="upload-zone">
            <h3 style="color: #8B7355; font-family: Lora, serif;">Drag & Drop Your Documents</h3>
            <p style="color: #704214; margin-top: 1rem;">Supported formats: PDF, JPG, PNG, TIFF</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'tif'],
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            st.markdown("""
            <div class="info-box">
                <strong>📄 File Details</strong><br>
                Successfully uploaded: <strong>{}</strong><br>
                File size: <strong>{:.2f} MB</strong>
            </div>
            """.format(uploaded_file.name, uploaded_file.size / (1024*1024)), unsafe_allow_html=True)
            
            # Show preview
            if uploaded_file.type.startswith('image'):
                st.markdown("<div class='document-preview'>", unsafe_allow_html=True)
                st.image(uploaded_file, caption="Document Preview", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Processing section
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                if st.button("🚀 Process Document", use_container_width=True):
                    process_document(uploaded_file)
    
    with col2:
        st.markdown("""
        <div class="info-box">
            <h4 style="margin-top: 0; color: #5C4033;">💡 Processing Tips</h4>
            <ul style="line-height: 1.8;">
                <li>Ensure documents are well-lit and in focus</li>
                <li>Higher resolution images yield better results</li>
                <li>Multi-page PDFs are fully supported</li>
                <li>Pre-revolutionary cursive: 90%+ accuracy</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box" style="background: rgba(139, 195, 74, 0.1); border-left: 5px solid #8BC34A;">
            <h4 style="margin-top: 0; color: #5C4033;">✨ Special Features</h4>
            <ul style="line-height: 1.8;">
                <li>Church registry books (метрические книги)</li>
                <li>Census records (ревизские сказки)</li>
                <li>Birth & marriage certificates</li>
                <li>Property documents</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def process_document(file):
    """Simulate document processing with elegant progress indicators"""
    st.markdown("<div class='ornamental-divider'>◈ ◆ ◈</div>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #5C4033; font-family: Playfair Display, serif;'>⚙️ Processing Document</h3>", unsafe_allow_html=True)
    
    # Processing stages
    stages = [
        ("📸 Image Preprocessing", "Enhancing contrast and removing noise..."),
        ("🔤 Text Detection", "Identifying text regions and layout..."),
        ("✍️ Handwriting Recognition", "Analyzing pre-revolutionary script..."),
        ("🏷️ Metadata Extraction", "Extracting names, dates, and locations..."),
        ("💾 Database Integration", "Indexing and storing results...")
    ]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, (stage, description) in enumerate(stages):
        status_text.markdown(f"""
        <div class="info-box fade-in">
            <strong>{stage}</strong><br>
            {description}
        </div>
        """, unsafe_allow_html=True)
        
        time.sleep(0.8)
        progress_bar.progress((idx + 1) / len(stages))
    
    # Results
    st.markdown("""
    <div class="success-box fade-in">
        <h3 style="margin-top: 0; color: #558B2F;">✅ Processing Complete!</h3>
        <p style="color: #33691E; font-size: 1.1rem; margin: 0;">
            Document successfully processed and indexed into the archive database.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display extracted data
    display_results()

def display_results():
    """Display processing results in elegant format"""
    st.markdown("<div class='ornamental-divider'>◈ ◆ ◈</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #5C4033; font-family: Playfair Display, serif;'>📋 Extracted Information</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title" style="font-size: 1.4rem;">Personal Information</div>
            <table style="width: 100%; margin-top: 1rem; font-family: Source Sans Pro, sans-serif; line-height: 2;">
                <tr><td><strong>Full Name:</strong></td><td>Иван Петрович Соколов</td></tr>
                <tr><td><strong>Birth Date:</strong></td><td>15 марта 1885 года</td></tr>
                <tr><td><strong>Birth Place:</strong></td><td>Москва, Пречистенская часть</td></tr>
                <tr><td><strong>Father:</strong></td><td>Петр Иванович Соколов</td></tr>
                <tr><td><strong>Mother:</strong></td><td>Мария Александровна Соколова</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title" style="font-size: 1.4rem;">Document Metadata</div>
            <table style="width: 100%; margin-top: 1rem; font-family: Source Sans Pro, sans-serif; line-height: 2;">
                <tr><td><strong>Document Type:</strong></td><td>Метрическая книга</td></tr>
                <tr><td><strong>Record Number:</strong></td><td>№ 47</td></tr>
                <tr><td><strong>Church:</strong></td><td>Церковь Николая Чудотворца</td></tr>
                <tr><td><strong>Archive Fond:</strong></td><td>Ф. 203, Оп. 745</td></tr>
                <tr><td><strong>Confidence:</strong></td><td>95.3%</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
    
    # Recognized text preview
    st.markdown("<div class='ornamental-divider'>◈ ◆ ◈</div>", unsafe_allow_html=True)
    
    with st.expander("📜 View Full Recognized Text", expanded=False):
        st.markdown("""
        <div style="background: white; padding: 2rem; border: 2px solid #D4AF37; border-radius: 10px; font-family: Lora, serif; line-height: 1.8; color: #5C4033;">
            <em>Тысяча восемьсот восемьдесят пятаго года марта пятнадцатаго дня в метрическую книгу 
            церкви Святаго Николая Чудотворца записано: родился младенецъ мужеска пола, названъ Иваномъ, 
            крещенъ священникомъ Василiемъ Петровымъ. Родители: дворянинъ Петръ Ивановичъ Соколовъ и 
            законная жена его Марiя Александровна, православные...</em>
        </div>
        """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("📥 Export to Database", use_container_width=True)
    with col2:
        st.button("📄 Download Report", use_container_width=True)
    with col3:
        st.button("🔄 Process Another", use_container_width=True)

def render_sidebar():
    """Render elegant sidebar navigation"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 2rem 0;">
            <h2 style="font-family: Playfair Display, serif; color: #5C4033; margin: 0;">Навигация</h2>
            <div style="color: #8B7355; margin-top: 0.5rem;">◈ ◆ ◈</div>
        </div>
        """, unsafe_allow_html=True)
        
        page = st.radio(
            "Раздел",
            ["🏠 Главная", "📤 Загрузить документы", "📊 Статистика", "🔍 Поиск по архиву", "⚙️ Настройки", "📚 О системе"],
            label_visibility="visible",
            index=0
        )
        st.markdown("<hr style='border: 1px solid rgba(139, 115, 85, 0.3);'>", unsafe_allow_html=True)
        
        # Active Quick Actions
        st.markdown("""
        <div style='background: rgba(212, 175, 55, 0.1); padding: 1.5rem; border-radius: 10px; border: 1px solid rgba(139, 115, 85, 0.3);'>
            <h4 style='margin:0 0 1rem 0; color: #5C4033; font-family: Playfair Display, serif;'>Быстрые действия</h4>
            <button style='margin: 0.2rem; width: 100%; background: #8B7355; color: white; border-radius: 8px; border: none; padding: 0.7rem 0; font-family: Source Sans Pro, sans-serif; font-size: 1.07rem;' onclick="window.location.href='/batch'">⚡ Пакетная обработка</button>
            <button style='margin: 0.2rem; width: 100%; background: #D4AF37; color: white; border-radius: 8px; border: none; padding: 0.7rem 0; font-family: Source Sans Pro, sans-serif; font-size: 1.07rem;' onclick="window.location.href='/recent'">📁 Недавние документы</button>
            <button style='margin: 0.2rem; width: 100%; background: #5C4033; color: white; border-radius: 8px; border: none; padding: 0.7rem 0; font-family: Source Sans Pro, sans-serif; font-size: 1.07rem;' onclick="window.location.href='/api'">🔗 Доступ к API</button>
            <button style='margin: 0.2rem; width: 100%; background: #8BC34A; color: white; border-radius: 8px; border: none; padding: 0.7rem 0; font-family: Source Sans Pro, sans-serif; font-size: 1.07rem;' onclick="window.location.href='/docs'">📖 Документация</button>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<hr style='border: 1px solid rgba(139, 115, 85, 0.3);'>", unsafe_allow_html=True)
        # Quick actions
        st.markdown("""
        <div style="background: rgba(212, 175, 55, 0.1); padding: 1.5rem; border-radius: 10px; border: 1px solid rgba(139, 115, 85, 0.3);">
            <h4 style="margin: 0 0 1rem 0; color: #5C4033; font-family: Playfair Display, serif;">Quick Actions</h4>
            <div style="line-height: 2; font-family: Source Sans Pro, sans-serif; color: #704214;">
                ⚡ Batch Processing<br>
                📁 Recent Documents<br>
                🔗 API Access<br>
                📖 Documentation
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin: 2rem 0;'><hr style='border: 1px solid rgba(139, 115, 85, 0.3);'></div>", unsafe_allow_html=True)
        
        # System status
        st.markdown("""
        <div style="background: rgba(139, 195, 74, 0.1); padding: 1.5rem; border-radius: 10px; border: 1px solid rgba(139, 195, 74, 0.5);">
            <h4 style="margin: 0 0 1rem 0; color: #558B2F; font-family: Playfair Display, serif;">System Status</h4>
            <div style="font-family: Source Sans Pro, sans-serif; color: #33691E; line-height: 1.8;">
                ✅ All Systems Operational<br>
                🟢 API: Online<br>
                🟢 Database: Connected<br>
                🟢 ML Models: Ready
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style="margin-top: 3rem; text-align: center; font-family: Source Sans Pro, sans-serif; color: #8B7355; font-size: 0.85rem;">
            <div style="margin-bottom: 0.5rem;">◈ ◆ ◈</div>
            Moscow Archives System<br>
            v2.0.1 | 2025<br>
            <div style="margin-top: 1rem; font-size: 0.75rem;">
                Powered by AI & Machine Learning
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_footer():
    """Render elegant footer"""
    st.markdown("""
    <div class="archive-footer">
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
    st.markdown("""
    <div class='stat-card fade-in' style='margin-top: 2rem;'>
        <div style='font-family: Playfair Display, serif; font-size: 2rem; color: #5C4033; letter-spacing: 2px;'>🎯 Точность Модели</div>
        <div style='font-family: Source Sans Pro, sans-serif; font-size:1.2rem; color:#704214; margin-top:1rem;'>
            Наш искусственный интеллект успешно распознал <strong>94,2%</strong> полей в архивных документах за последний месяц.
            <br>Оценка на основе <strong>2&nbsp;847</strong> реальных документов периода 1772-1917 гг.<br>
            <span style='color: #8BC34A; font-weight: 600;'>Достоверность результатов подтверждена экспертами архива.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main application
def main():
    """Main application entry point"""
    # Load custom CSS
    load_custom_css()
    page = render_sidebar()
    render_header()
    render_accuracy_card()
    render_features()
    render_upload_section()
    render_footer()

if __name__ == "__main__":
    main()
