FROM node:20-slim AS build-stage

# Set working directory for frontend build
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build


FROM python:3.10-slim

WORKDIR /app

# Install Python dependencies and build files from Frontend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY --from=build-stage /app/frontend/dist ./frontend/dist

EXPOSE 8080
CMD ["python3", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]