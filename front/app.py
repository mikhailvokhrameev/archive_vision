import streamlit as st
import os
import shutil
import json
from PIL import Image
import requests
from io import BytesIO

import os

# Подключение к бекэнду
def get_api_base():
    # 1) сначала пробуем переменную окружения (удобно для Docker/CI)
    env = os.environ.get("API_BASE")
    if env:
        return env

    # 2) затем пробуем st.secrets, но в try/except — чтобы не падать, если файла нет
    try:
        api = st.secrets.get("api_base")  # если secrets нет — может выбросить исключение
        if api:
            return api
    except Exception:
        pass

    # 3) fallback
    return "http://127.0.0.1:8000"

API_BASE = get_api_base()

st.title("Рукописный перевод архивных документов (интеграция с API)")

# Состояние
if 'processed' not in st.session_state:
    st.session_state.processed = {}  # name -> {text, record_id, path, ...}
if 'total_processed' not in st.session_state:
    st.session_state.total_processed = 0
if 'total_session' not in st.session_state:
    st.session_state.total_session = 0

option = st.radio("Способ загрузки", ("Загрузить файлы", "Указать директорию"))
files = []
temp_dir = "temp_uploads"
os.makedirs(temp_dir, exist_ok=True)

if option == "Загрузить файлы":
    uploaded_files = st.file_uploader("Загрузите изображения (JPG, JPEG, PDF)", type=['jpg', 'jpeg', 'pdf'], accept_multiple_files=True)
    if uploaded_files:
        for uf in uploaded_files:
            path = os.path.join(temp_dir, uf.name)
            with open(path, "wb") as f:
                f.write(uf.getvalue())
            if not uf.name.lower().endswith(('.jpg', '.jpeg', '.pdf')):
                st.error(f"Файл {uf.name} не является изображением JPG/JPEG/PDF и был пропущен.")
                continue
            files.append((uf.name, path, uf))

elif option == "Указать директорию":
    directory = st.text_input("Путь к директории с изображениями")
    if directory and os.path.isdir(directory):
        for f in os.listdir(directory):
            if f.lower().endswith(('.jpg', '.jpeg')):
                files.append((f, os.path.join(directory, f), None))
            else:
                st.error(f"Файл {f} в директории не является изображением JPG/JPEG и был пропущен.")

if files:
    st.write(f"Обнаружено {len(files)} документов для обработки.")
    st.session_state.total_session = len(files)

    if st.button("Обработать (отправить на бэкенд)"):
        progress_bar = st.progress(0)
        for i, (name, path, uploadfile_obj) in enumerate(files):
            try:
                # Если у нас есть UploadFile-объект (из streamlit), используем его содержимое
                if uploadfile_obj is not None:
                    files_payload = {"file": (name, uploadfile_obj.getvalue())}
                else:
                    # читаем локальный файл
                    with open(path, "rb") as f:
                        files_payload = {"file": (name, f.read())}
                # requests expects file-like or tuple. Use BytesIO wrapper:
                fp = BytesIO(files_payload["file"][1])
                # !!! Будет возникать ошибка 500 -> после доавбления модели изменить на эндпоинт /recognize !!!
                response = requests.post(f"{API_BASE}/recognize/", files={"file": (name, fp, "application/octet-stream")})
                if response.status_code == 200:
                    j = response.json()
                    record_id = j.get("record_id")
                    text = j.get("text", "")
                    st.session_state.processed[name] = {
                        'text': text,
                        'accuracy': None,
                        'low_conf': None,
                        'bboxes': [],
                        'path': path,
                        'record_id': record_id
                    }
                else:
                    st.error(f"Ошибка распознавания файла {name}: {response.status_code} {response.text}")
            except Exception as e:
                st.error(f"Ошибка при отправке файла {name}: {e}")
            progress_bar.progress((i + 1) / len(files))
        st.session_state.total_processed += len(files)
        st.success("Отправка и обработка завершены!")

st.write(f"Общее количество обработанных документов (за сеанс): {st.session_state.total_session}")
st.write(f"Общее количество обработанных документов (всего): {st.session_state.total_processed}")

# Показ результатов
if st.session_state.processed:
    for name, data in st.session_state.processed.items():
        st.subheader(f"Документ: {name}")
        if data.get('accuracy') is not None:
            st.write(f"Уровень уверенности в распознавании: {data['accuracy']}%")
        if data.get('low_conf') is not None:
            st.write(f"Количество элементов с низкой уверенностью: {data['low_conf']}")

        col1, col2 = st.columns(2)
        with col1:
            try:
                img = Image.open(data['path'])
                st.image(img, caption="Оригинальный образ", use_container_width=True)
            except Exception:
                st.write("Не удалось открыть изображение локально.")

        with col2:
            edited_text = st.text_area("Распознанный текст (верифицируйте и корректируйте)", data['text'], height=300, key=f"text_{name}")
            if edited_text != data['text']:
                st.session_state.processed[name]['text'] = edited_text
                st.write("Локальные правки сохранены. Нажмите кнопку ниже, чтобы отправить их на бэкенд.")

            if st.button(f"Сохранить правки в БД ( {name} )"):
                rec_id = data.get("record_id")
                if not rec_id:
                    st.error("Record ID отсутствует — не удалось обновить на сервере.")
                else:
                    payload = {"text": edited_text, "filename": name}
                    r = requests.put(f"{API_BASE}/recognitions/{rec_id}", json=payload)
                    if r.status_code == 200:
                        st.success("Правки успешно сохранены на сервере.")
                    else:
                        st.error(f"Ошибка сохранения: {r.status_code} {r.text}")

        # Показанные атрибуты (если есть)
        if data.get('bboxes'):
            st.write("Извлеченные атрибуты (для верификации):")
            for bbox in data['bboxes']:
                st.write(f"- {bbox['text']} (уверенность: {bbox.get('conf', 0)*100:.1f}%)")

# Выгрузка результатов локально
if st.session_state.processed:
    st.header("Выгрузка результатов")
    attributes = st.multiselect("Выберите атрибуты для выгрузки", ["ФИО", "Даты", "Адреса", "Архивные шифры", "Весь текст"])
    format = st.selectbox("Формат выгрузки", ["JSON", "CSV", "TXT"])

    if st.button("Сформировать выгрузку"):
        export_data = {}
        for name, data in st.session_state.processed.items():
            export_data[name] = {
                'text': data['text'] if "Весь текст" in attributes or not attributes else "",
                'extracted': {"ФИО": "Иванов Иван Иванович"} if "ФИО" in attributes else {},
            }

        if format == "JSON":
            export_str = json.dumps(export_data, ensure_ascii=False, indent=4)
            mime = "application/json"
            file_ext = ".json"
        elif format == "CSV":
            export_str = "Документ,Текст\n" + "\n".join([f"{name},{data['text'].replace(chr(10),' ')}" for name, data in export_data.items()])
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

# Очистка временных файлов
if st.button("Очистить временные файлы"):
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass
    st.session_state.processed = {}
    st.write("Временные файлы удалены и сессия очищена.")
