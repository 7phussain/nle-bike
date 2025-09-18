#!/bin/bash

# NLE Bike Development Server
echo "🚀 Starting NLE Bike Development Server..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Start the FastAPI server
echo "🌐 Starting server at http://localhost:8000"
uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload
