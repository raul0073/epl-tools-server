# Use Python 3.12 base image (soccerdata compatible)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y build-essential gcc libffi-dev && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app
COPY . .

# Expose port (Render will inject $PORT, but 8080 is safe default)
EXPOSE 8080

# Run FastAPI app (shell form so $PORT expands correctly)
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
