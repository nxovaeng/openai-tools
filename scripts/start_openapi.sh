#!/bin/bash

# Start OpenAPI Server for Open WebUI integration
# This script starts the FastAPI server with OpenAPI documentation

set -e

echo "🚀 Starting Xray + Nginx OpenAPI Server..."
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f "config/.env" ]; then
    echo "⚙️  Creating .env file from example..."
    cp config/.env.example config/.env
    echo ""
    echo "⚠️  Please edit config/.env file to configure API_KEY and other settings"
    echo ""
fi

# Start server
echo "✅ Starting OpenAPI server..."
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📖 ReDoc: http://localhost:8000/redoc"
echo "🔗 OpenAPI Schema: http://localhost:8000/openapi.json"
echo ""
echo "🔌 To integrate with Open WebUI:"
echo "   1. Open Open WebUI Settings"
echo "   2. Go to Tools section"
echo "   3. Add tool server: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Set PYTHONPATH to include src directory
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

python -m src.api.openapi_server
