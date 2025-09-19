# Use a standard Python base image
FROM python:3.12.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements file and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./backend /app/backend
COPY ./frontend /app/frontend

EXPOSE 8080

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]