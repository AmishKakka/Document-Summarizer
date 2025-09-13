# Use a standard Python base image
FROM python:3.12.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./backend /app/backend
COPY ./frontend /app/frontend

# Expose the port the app will run on
EXPOSE 8080

# The command to run the Uvicorn server for FastAPI
# '$PORT' is automatically supplied by services like Cloud Run
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]