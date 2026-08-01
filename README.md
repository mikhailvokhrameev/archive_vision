# "Archive Vision" Web Service

This repository contains the source code for a web service designed for automated transcription of archival documents from Moscow archives, contributing to the preservation of historical heritage.

<div align="center">
<img src="https://github.com/user-attachments/assets/ddbb62d4-cbc2-423e-aafd-e95b3cb7c1b4" width="600"><br>
<em>Main Page</em>
</div>

---

### Why did we create this project?

We were interested in working with modern OCR models, specifically **TrOCR**, annotating a dataset with archival images, and gaining practical experience in building a full-fledged web service powered by AI models.

---

### Technologies Used:

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

Frontend & Visualization

* Streamlit

Database

* PostgreSQL

---

### Installation and Launch using Docker (Recommended)

1. **Clone the repository:**

   ```bash
   git clone https://github.com/mikhailvokhrameev/archive_vision.git
   cd archive_vision
   ```
2. **Install Docker depending on your OS:**

   * Windows: Install Docker Desktop following the [official instructions](https://docs.docker.com/desktop/setup/install/windows-install/).
   * macOS: Install Docker Desktop following the [official instructions](https://docs.docker.com/desktop/setup/install/mac-install/).
   * Linux: Install Docker Engine following the [official instructions](https://docs.docker.com/engine/install/).
3. **Run docker-compose:**

   **Important:** All commands must be executed from the root folder of the project.

   ```bash
   docker-compose up --build # build and run
   docker-compose up # run
   ```

   To open the frontend, navigate to: http://localhost:8501/

---

### Alternative Option (without Docker):

To set up the project environment, follow these steps:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/mikhailvokhrameev/archive_vision.git
   cd archive_vision
   ```
2. **Create and activate a virtual environment (recommended):**

   ```bash
   # Create environment
   python3 -m venv venv

   # Activation on macOS/Linux:
   source venv/bin/activate

   # Activation on Windows:
   venv\Scripts\activate
   ```
3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

#### **Running the Application:**

1. **Start backend**

   This script starts the backend at http://127.0.0.1:8001.

   ```bash
   uvicorn main:app --reload --host 127.0.0.1 --port 8001
   ```
2. **Start frontend**

   This script starts the frontend at http://127.0.0.1:8000. To change the port or IP, add the server URL to the `API_BASE_URL` environment variable in the docker file.

   ```bash
   streamlit run ./front/app.py
   ```
3. **Database Configuration**

   PostgreSQL is used as the database. To connect the backend to the database, create a `.env` file in the `backend` folder and add the variable:
   `DATABASE_URL="postgresql://user:password@localhost:5432/db_name"`
4. **Using the Service**

   By default, the service operates at http://127.0.0.1:8501. To upload and process a document, upload an image file of the document page via the web interface.
