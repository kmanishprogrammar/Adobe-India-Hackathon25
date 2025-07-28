FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/src/

# Set environment variables
ENV PYTHONPATH=/app
ENV INPUT_DIR=/app/input
ENV OUTPUT_DIR=/app/output

# Create directories
RUN mkdir -p /app/input /app/output

# Set the entrypoint
ENTRYPOINT ["python", "-m", "src.main"]
