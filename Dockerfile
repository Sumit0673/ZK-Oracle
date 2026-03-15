# Use Python 3.12 (stable and common for cloud)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lib/lists/*

# Copy requirements and install
COPY agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project structure 
# (Needed because api.py imports from bridge.py which imports from integration folder)
COPY . .

# Set environment variables
ENV PYTHONPATH="/app/agent:/app/integration"
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Start the application
CMD ["python", "agent/api.py"]
