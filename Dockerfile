# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Node.js for MongoDB MCP server
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest \
    && npm install -g @mongodb-js/mongodb-mcp-server \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY src/agent.py agent.py
COPY src/index_docs.py index_docs.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Run the Flask application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 agent:app
