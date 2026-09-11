FROM python:3.11-slim

WORKDIR /app

# Install Tesseract OCR
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Keep backend inside /app/backend
COPY backend /app/backend

# Keep frontend at /app/frontend
COPY frontend /app/frontend

# Sample outputs
COPY sample_outputs /app/sample_outputs

# Upload directory
RUN mkdir -p /app/uploads

# Run application from backend directory
WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]