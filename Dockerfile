FROM python:3.10-slim

# Install system dependencies (LibreOffice, Tesseract OCR, and utilities)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    g++ \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up app directory
WORKDIR /code

# Copy requirements and install python packages
COPY ./backend/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy source code
COPY ./backend /code/backend
COPY ./run.py /code/run.py

# Create directory structures for uploads/outputs and set correct permissions
RUN mkdir -p /code/uploads/media /code/output && chmod -R 777 /code/uploads /code/output

# Set environment variable to make FastAPI listen on port 7860 (Hugging Face requirement)
ENV PORT=7860
ENV ENV=production
EXPOSE 7860

# Run using uvicorn
CMD ["python", "run.py"]
