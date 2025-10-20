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