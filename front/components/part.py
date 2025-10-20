import streamlit as st
import json
import time
import requests
from PIL import Image
from datetime import datetime
from api.backend_client import upload_file_to_backend, transcribe_file, wait_for_processing, update_transcript, get_transcript, get_all_files_count, get_all_transcripts, save_corrections, API_BASE
# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Moscow Archives | Document Recognition",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
            "description": """Используем модель TrOCR, дообученную на 73830 сегментах рукописных текстов на русском языке""",
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
    """Display and edit transcribed results with a toggleable edit mode."""
    if not st.session_state.get("processed_files"):
        return

    st.markdown("<div class='ornamental-divider'>◈ ◆ ◈</div>", unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align: center; color: #5C4033; font-family: Playfair Display, serif;'>📋 Результаты и Коррекция</h2>",
        unsafe_allow_html=True
    )

    for file_name, data in st.session_state.processed_files.items():
        file_id = data['file_id']

        # Initialize edit mode state for each file if it doesn't exist
        if f"edit_mode_{file_id}" not in st.session_state:
            st.session_state[f"edit_mode_{file_id}"] = False

        with st.expander(f"📄 **{file_name}** (File ID: {file_id})", expanded=True):
            col1, col2 = st.columns([2, 3])

            # --- Image Preview ---
            with col1:
                try:
                    if data["path"].lower().endswith('.pdf'):
                        st.info("📕 PDF-файл (предпросмотр недоступен в этой секции)")
                    else:
                        img = Image.open(data["path"])
                        st.image(img, caption="Оригинал документа", use_container_width=True)
                except Exception as e:
                    st.warning(f"⚠️ Не удалось загрузить изображение для предпросмотра: {e}")

            # --- Display/Edit Area ---
            with col2:
                raw_data = data.get("raw_data", {})
                recognized_fragments = raw_data.get("recognized_words", [])

                if not st.session_state[f"edit_mode_{file_id}"]:
                    # --- VIEW MODE ---
                    st.markdown("<h4 style='color: #5C4033;'>Распознанный текст</h4>", unsafe_allow_html=True)
                    
                    full_text = " ".join([f.get('text', '') for f in recognized_fragments])
                    
                    st.markdown(f"""
                    <div style='height: 400px; overflow-y: auto; padding: 1rem; 
                                 background: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 8px; 
                                 color: #333; font-family: Lora, serif; line-height: 1.8;'>
                        {full_text or "Текст не распознан."}
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("✏️ Изменить расшифровку", key=f"edit_btn_{file_id}", use_container_width=True):
                        st.session_state[f"edit_mode_{file_id}"] = True
                        st.rerun()

                else:
                    # --- EDIT MODE ---
                    st.markdown("<h4 style='color: #5C4033;'>Редактирование фрагментов</h4>", unsafe_allow_html=True)
                    
                    if not recognized_fragments:
                        st.warning("Нет распознанных фрагментов для редактирования.")
                        if st.button("Отмена", key=f"cancel_btn_{file_id}_no_frag"):
                            st.session_state[f"edit_mode_{file_id}"] = False
                            st.rerun()
                        continue

                    # Initialize fragment states if not present
                    if f"fragments_{file_id}" not in st.session_state:
                        st.session_state[f"fragments_{file_id}"] = {
                            f['fragment_id']: f['text'] for f in recognized_fragments
                        }

                    # Display each fragment as a text input
                    for fragment in recognized_fragments:
                        fragment_id = fragment['fragment_id']
                        edited_text = st.text_input(
                            label=f"Фрагмент {fragment_id}",
                            value=st.session_state[f"fragments_{file_id}"].get(fragment_id, fragment['text']),
                            key=f"frag_{file_id}_{fragment_id}"
                        )
                        st.session_state[f"fragments_{file_id}"][fragment_id] = edited_text

                    # Action buttons for edit mode
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("💾 Сохранить исправления", key=f"save_btn_{file_id}", use_container_width=True):
                            corrections_to_save = []
                            original_map = {f['fragment_id']: f['text'] for f in recognized_fragments}
                            
                            for frag_id, edit_text in st.session_state[f"fragments_{file_id}"].items():
                                if edit_text != original_map.get(frag_id):
                                    corrections_to_save.append({"fragment_id": frag_id, "corrected_text": edit_text})
                            
                            if corrections_to_save:
                                with st.spinner("Сохранение..."):
                                    result = save_corrections(file_id, corrections_to_save)
                                    if result["success"]:
                                        st.success(f"✅ Сохранено {len(corrections_to_save)} исправлений!")
                                        # Exit edit mode after saving
                                        st.session_state[f"edit_mode_{file_id}"] = False
                                        # Update the base data to reflect changes without a full rerun
                                        for frag in recognized_fragments:
                                            if frag['fragment_id'] in st.session_state[f"fragments_{file_id}"]:
                                                frag['text'] = st.session_state[f"fragments_{file_id}"][frag['fragment_id']]
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Ошибка: {result['error']}")
                            else:
                                st.info("Нет изменений для сохранения.")
                    
                    with btn_col2:
                        if st.button("Отмена", key=f"cancel_btn_{file_id}", use_container_width=True):
                            # Discard changes and exit edit mode
                            del st.session_state[f"fragments_{file_id}"]
                            st.session_state[f"edit_mode_{file_id}"] = False
                            st.rerun()


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