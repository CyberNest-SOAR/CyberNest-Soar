# Use stable Python 3.10
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .

RUN sed -i 's/\r$//' requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy app code (includes artifacts, data, client_secret.json, etc.)
COPY . .

# Prevent log buffering
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 8000

# Run the unified CyberNest backend app with auto-reload for development convenience.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
