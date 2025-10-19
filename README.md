# Веб-сервис "Archive Vision"

Данный репозиторий содержит исходный код веб‑сервиса для автоматизированной расшифровки архивных документов московских архивов, что способствует сохранению исторического наследия.

<div align="center">
<img src="https://github.com/user-attachments/assets/ddbb62d4-cbc2-423e-aafd-e95b3cb7c1b4" width="600"><br>
<em>Главная страница</em>
</div>

---

### Почему мы делали этот проект?

Нам было интересно поработать с современными моделями OCR, в частности **TrOCR**, произвести разметку датасета с архивными изображениями, а также получить опыт создания полноценного веб-сервиса с применением моделей ИИ.

---

### Используемые технологии:

Backend & API
* Python
* FastAPI
* Uvicorn
* Pydantic

Machine Learning & Data Science
* PyTorch
* Hugging Face Transformers
* NumPy & SciPy
* OpenCV & Pillow
* pdf2image

Frontend & Визуализация
* Streamlit

База Данных
* PostgreSQL


---

### Установка и запуск с использованием Docker (рекомендуется)

1. **Клонируйте репозиторий:**

   ```bash
   git clone https://github.com/mikhailvokhrameev/archive_vision.git
   cd archive_vision
   ```

2. **Установите Docker в зависимости от вашей ОС:**
   * Windows: Установите Docker Desktop по [официальной инструкции](https://docs.docker.com/desktop/setup/install/windows-install/).
   * macOS: Установите Docker Desktop по [официальной инструкции](https://docs.docker.com/desktop/setup/install/mac-install/).
   * Linux: Установите Docker Engine по [официальной инструкции](https://docs.docker.com/engine/install/).

3. **Запустите docker-compose:**

   **Важно:** Все команды должны запускаться из корневой папки проекта.
   
   ```bash
   docker-compose up --build # build and run
   docker-compose up #run
   ```

---

### Альтернативный вариант (без Docker):

Для настройки среды проекта выполните следующее:

1. **Клонируйте репозиторий:**

   ```bash
   git clone https://github.com/mikhailvokhrameev/archive_vision.git
   cd archive_vision
   ```
   
2. **Создайте и активируйте виртуальное окружение (рекомендуется):**

   ```bash
   # Создание окружения
   python3 -m venv venv

   # Активация на macOS/Linux:
   source venv/bin/activate

   # Активация на Windows:
   venv\Scripts\activate
   ```
3. **Установите зависимости:**

   ```bash
   pip install -r requirements.txt
   ```

#### **Запуск:**

 1. **Запуск backend**

      Этот скрипт запускает backend по адресу http://127.0.0.1:8001.
      ```bash
      uvicorn main:app --reload --host 127.0.0.1 --port 8001
      ```

2. **Запуск frontend**

   Этот скрипт запускает frontend по адресу http://127.0.0.1:8000. Для изменения порта или IP требуется добавить в переменные окружения в docker файле API_BASE_URL ссылку на сервер.
   
   ```bash
   streamlit run ./front/app.py
   ```

3. **Настройка БД**

   В качестве базы данных используется PostgreSQL. Скрипт для создания таблиц в базе данных представлен в файле generate_db.sql. Для связи backend и базы данных требуется в файле backend\database.py изменить:
   
   * DB_USER - имя администратора БД;
   * DB_PASS - пароль администратора;
   * DB_HOST - IP адрес БД;
   * DB_PORT - порт для подключения к БД;
   * DB_NAME - название базы данных.

4. **Работа с сервисом**

   По умолчанию работа сервиса производится по адресу http://127.0.0.1:8501. Для загрузки и обработки документа требуется загрузить файл с изображением страницы документа через веб интерфейс.
