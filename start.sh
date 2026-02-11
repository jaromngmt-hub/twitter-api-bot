#!/bin/sh
# Start script for Render deployment

if [ -n "$PORT" ]; then
    echo "Starting web API on port $PORT..."
    uvicorn api:app --host 0.0.0.0 --port $PORT
else
    echo "Starting CLI monitor..."
    python main.py run
fi
