FROM python:3.12
WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY ./archive_vision .

CMD bash -c "uvicorn back.main:app --host 0.0.0.0 --port 8000 & streamlit run front/app.py --server.port=8501 --server.address=0.0.0.0"
