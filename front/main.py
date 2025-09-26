import streamlit as st
import os
import shutil
import json
from PIL import Image  # Requires pillow installation: pip install pillow
# For real OCR, install easyocr or pytesseract: pip install easyocr or pip install pytesseract
# For PDF handling, install pdf2image: pip install pdf2image (requires poppler)
# For image preprocessing, install opencv-python: pip install opencv-python
# Note: All these are open-source and can be used offline.

# Mock processing function. In real implementation, replace with actual preprocessing and OCR.
# Example: Use OpenCV for preprocessing (deskew, contrast), EasyOCR or Tesseract for recognition.
def process_file(file_path):
    # Mock values
    recognized_text = "Это пример распознанного текста из документа. ФИО: Иванов Иван Иванович. Дата: 1905-01-01. Адрес: Москва, ул. Тверская. Архивный шифр: Ф.123 О.4 Д.56."
    accuracy = 85  # Mock accuracy in %
    low_conf_elements = 2  # Mock count of low-confidence elements
    # Mock bounding boxes for verification (list of dicts: {'text': str, 'bbox': [x1,y1,x2,y2], 'conf': float})
    bboxes = [
        {'text': 'Иванов Иван Иванович', 'bbox': [100, 100, 300, 150], 'conf': 0.95},
        {'text': '1905-01-01', 'bbox': [100, 200, 200, 250], 'conf': 0.85}
    ]
    return recognized_text, accuracy, low_conf_elements, bboxes

# For self-learning mock: Store corrections in a file for 'retraining' simulation.
CORRECTIONS_FILE = "corrections.json"
if not os.path.exists(CORRECTIONS_FILE):
    with open(CORRECTIONS_FILE, 'w') as f:
        json.dump({}, f)

def load_corrections():
    with open(CORRECTIONS_FILE, 'r') as f:
        return json.load(f)

def save_correction(file_name, original_text, corrected_text):
    corrections = load_corrections()
    corrections[file_name] = {'original': original_text, 'corrected': corrected_text}
    with open(CORRECTIONS_FILE, 'w') as f:
        json.dump(corrections, f)
    # In real: Use this data to fine-tune model offline, e.g., with torch.

# Main app
st.title("Рукописный перевод архивных документов")

# Session state for persistence
if 'processed' not in st.session_state:
    st.session_state.processed = {}
if 'total_processed' not in st.session_state:
    st.session_state.total_processed = 0
if 'total_session' not in st.session_state:
    st.session_state.total_session = 0

# Upload option
option = st.radio("Способ загрузки", ("Загрузить файлы", "Указать директорию"))

files = []
temp_dir = "temp_uploads"
os.makedirs(temp_dir, exist_ok=True)

if option == "Загрузить файлы":
    uploaded_files = st.file_uploader("Загрузите образы (JPG, JPEG, TIFF, PDF)", type=['jpg', 'jpeg', 'tiff', 'pdf'], accept_multiple_files=True)
    if uploaded_files:
        for uf in uploaded_files:
            path = os.path.join(temp_dir, uf.name)
            with open(path, "wb") as f:
                f.write(uf.getvalue())
        files = [(uf.name, path) for uf in uploaded_files]

elif option == "Указать директорию":
    directory = st.text_input("Путь к директории с образами")
    if directory and os.path.isdir(directory):
        for f in os.listdir(directory):
            if f.lower().endswith(('.jpg', '.jpeg', '.tiff', '.pdf')):
                files.append((f, os.path.join(directory, f)))

if files:
    st.write(f"Обнаружено {len(files)} документов для обработки.")
    st.session_state.total_session = len(files)

    if st.button("Обработать"):
        progress_bar = st.progress(0)
        for i, (name, path) in enumerate(files):
            # Process (mock or real)
            text, accuracy, low_conf, bboxes = process_file(path)
            st.session_state.processed[name] = {
                'text': text,
                'accuracy': accuracy,
                'low_conf': low_conf,
                'bboxes': bboxes,
                'path': path
            }
            progress_bar.progress((i + 1) / len(files))
        st.session_state.total_processed += len(files)
        st.success("Обработка завершена!")

# Display stats
st.write(f"Общее количество обработанных документов (за сеанс): {st.session_state.total_session}")
st.write(f"Общее количество обработанных документов (всего): {st.session_state.total_processed}")

# Verification section
if st.session_state.processed:
    for name, data in st.session_state.processed.items():
        st.subheader(f"Документ: {name}")
        st.write(f"Уровень уверенности в распознавании: {data['accuracy']}%")
        st.write(f"Количество элементов с низкой уверенностью: {data['low_conf']}")

        # Side-by-side: Image and text
        col1, col2 = st.columns(2)
        with col1:
            # Display image (for PDF, would need conversion in real code)
            try:
                img = Image.open(data['path'])
                st.image(img, caption="Оригинальный образ", use_column_width=True)
            except:
                st.write("Предпросмотр PDF не поддерживается в mock. Используйте pdf2image для конвертации.")

        with col2:
            edited_text = st.text_area("Распознанный текст (верифицируйте и корректируйте)", data['text'], height=300, key=f"text_{name}")
            if edited_text != data['text']:
                save_correction(name, data['text'], edited_text)
                data['text'] = edited_text  # Update in session
                st.write("Правки сохранены! Модель 'дообучится' на этих данных (в реальной версии).")
                st.write("Пока вы сидите, я учусь!")

        # Mock attribute extraction display for verification
        st.write("Извлеченные атрибуты (для верификации):")
        for bbox in data['bboxes']:
            st.write(f"- {bbox['text']} (уверенность: {bbox['conf']*100:.1f}%)")

# Export section
if st.session_state.processed:
    st.header("Выгрузка результатов")
    attributes = st.multiselect("Выберите атрибуты для выгрузки", ["ФИО", "Даты", "Адреса", "Архивные шифры", "Весь текст"])
    format = st.selectbox("Формат выгрузки", ["JSON", "CSV", "TXT"])

    if st.button("Сформировать выгрузку"):
        # Mock export data
        export_data = {}
        for name, data in st.session_state.processed.items():
            export_data[name] = {
                'text': data['text'] if "Весь текст" in attributes else "",
                # Mock extracted attributes based on attributes selected
                'extracted': {"ФИО": "Иванов Иван Иванович"} if "ФИО" in attributes else {},
                # Add others similarly
            }

        if format == "JSON":
            export_str = json.dumps(export_data, ensure_ascii=False, indent=4)
            mime = "application/json"
            file_ext = ".json"
        elif format == "CSV":
            export_str = "Документ,Текст\n" + "\n".join([f"{name},{data['text']}" for name, data in export_data.items()])
            mime = "text/csv"
            file_ext = ".csv"
        else:
            export_str = "\n".join([f"{name}: {data['text']}" for name, data in export_data.items()])
            mime = "text/plain"
            file_ext = ".txt"

        st.download_button(
            label="Скачать выгрузку",
            data=export_str,
            file_name=f"archive_export{file_ext}",
            mime=mime
        )

# Cleanup temp on exit (manual for now)
if st.button("Очистить временные файлы"):
    shutil.rmtree(temp_dir)
    st.write("Временные файлы удалены.")