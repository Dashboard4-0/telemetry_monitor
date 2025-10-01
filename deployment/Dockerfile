# Dockerfile for PLC Data Collector

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py ./
COPY .env* ./

# Create configuration directories
RUN mkdir -p configs/plc_configs configs/tag_lists

# Set environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1
ENV DOCKER_ENV=true

# Default command - run interactive mode
CMD ["python", "main.py"]
