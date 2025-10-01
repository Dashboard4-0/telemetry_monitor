# Dockerfile for PLC Data Collector
# Build context should be set to the project root directory

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY deployment/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files from Core Application directory
# Using array syntax to handle spaces in directory name
COPY ["Core Application/", "./src/"]
RUN mv /app/src/*.py /app/ && rm -rf /app/src

# Copy environment files if they exist
COPY deployment/.env* ./

# Create configuration directories
RUN mkdir -p configs/plc_configs configs/tag_lists

# Set environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1
ENV DOCKER_ENV=true

# Default command - run interactive mode
CMD ["python", "main.py"]
