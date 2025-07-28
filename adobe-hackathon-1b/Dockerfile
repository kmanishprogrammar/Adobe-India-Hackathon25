FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Download the model
RUN python download_model.py

# Set the entrypoint
ENTRYPOINT ["python", "src/main.py"]

# Default command (can be overridden)
CMD ["--test_case", "Test case1"]