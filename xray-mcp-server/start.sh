#!/bin/bash
# Quick start script with virtual environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Xray Deployment API - Quick Start"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    
    echo "📥 Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ Virtual environment found"
    source venv/bin/activate
fi

# Check for API key
if [ ! -f ".env" ]; then
    echo "🔑 API key will be auto-generated on first run"
fi

# Start server
echo "🚀 Starting server on http://0.0.0.0:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
