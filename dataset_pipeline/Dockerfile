FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/raw data/processed data/outputs

ENV PYTHONPATH=/app
ENV REAL_DOWNLOADS_ENABLED=false
ENV FALLBACK_SYNTHETIC=true
ENV TOTAL_EVENTS_TARGET=50000

EXPOSE 8003

CMD ["python", "main.py", "--api", "--port", "8003"]
