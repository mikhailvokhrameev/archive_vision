"""
Moscow Archives Document Recognition System
A premium web interface for automated document processing and indexing
"""

import streamlit as st
from components.css import load_custom_css
from components.part import render_header, render_accuracy_card, render_features, render_upload_section, render_results_section, render_export_section, render_archive_page
from api.backend_client import initialize_session_state

# Main application
def main():
    """Main application entry point"""
    # Page configuration - must be first Streamlit command
    st.set_page_config(
        page_title="Moscow Archives | Document Recognition",
        page_icon="📜",
        layout="wide",
        initial_sidebar_state="expanded"
)
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
        initialize_session_state()
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