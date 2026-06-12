# Use stable Python 3.11
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /backend

# Install dependencies
COPY requirements.txt .

RUN sed -i 's/\r$//' requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy everything inside backend directly into the /backend WORKDIR
COPY . .

# Prevent log buffering
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 8000

# Run Uvicorn relative to the /backend base, tracking everything inside it
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/backend"]