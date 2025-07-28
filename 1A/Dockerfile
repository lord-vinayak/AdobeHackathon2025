# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script
COPY pdf_outline_extractor.py .

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Set the command to run the script
CMD ["python", "pdf_outline_extractor.py"]