FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (git, java, maven for replay execution)
RUN apt-get update && apt-get install -y \
    git \
    default-jdk-headless \
    maven \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
