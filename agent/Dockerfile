# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (needed for Web3 and crypto libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (to leverage Docker cache)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the agent code
COPY . .

# Expose the API port (so the Frontend can talk to it)
EXPOSE 8080

# Default command: Run the API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
