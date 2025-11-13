# Use stable Python 3.10
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .


# Copy artifacts (models, vectorizers, etc.)
COPY artifacts/ ./artifacts/

# Prevent log buffering
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 8000

# Run FastAPI app by default
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
