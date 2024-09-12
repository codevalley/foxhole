# Use the official Python 3.12 image from Docker Hub
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /workspace

# Copy the requirements files to the working directory
COPY requirements.txt requirements-dev.txt /workspace/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Install Redis CLI
RUN apt-get update && apt-get install -y redis-tools

# Install MinIO client
RUN curl https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc \
    && chmod +x /usr/local/bin/mc

# Expose FastAPI port
EXPOSE 8000
