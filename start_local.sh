#!/bin/bash

# 1. Build the frontend
echo "Building Frontend..."
cd frontend
npm run build
cd ..
echo "Frontend built successfully."

# 2. Start the backend (which now serves the frontend)
echo "Starting Backend..."
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload &
BACKEND_PID=$!
sleep 3

echo "Starting Frontend Dev Server..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo "Yeah!!!"
echo "  Backend:  http://localhost:8080"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait