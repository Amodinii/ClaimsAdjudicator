# Base Image
FROM python:3.10-slim

# Working directory
WORKDIR /app

# Install system dependencies for OpenCV/ImageHash
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copying requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copying the rest of the backend code
COPY . .

#Setting Environment Variables 
ENV UPLOAD_DIR=uploads

# Exposing the internal port
EXPOSE 8000

# Starting the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]