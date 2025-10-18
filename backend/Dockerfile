FROM python:3.12

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости сначала для кэширования
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаем директории для данных
RUN mkdir -p /app/data /app/data/transcripts

EXPOSE 8001

CMD ["python", "main.py"]