FROM python:3.11.7-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY setup.py .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install -e .

# Copy the rest of the application
COPY . .

# Make sure PYTHONPATH is set correctly
ENV PYTHONPATH=/app

# Run the API server
CMD cd src/api && python run_api.py --port ${PORT:-8080} 