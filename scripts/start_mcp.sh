#!/bin/bash

# Start MCP Server
# This script starts the FastMCP server for MCP protocol integration

set -e

echo "🚀 Starting Xray + Nginx MCP Server..."
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
    echo "⚠️  Please edit config/.env file to configure settings"
    echo ""
fi

# Start server
echo "✅ Starting MCP server..."
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Set PYTHONPATH to include src directory
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

python -m src.api.mcp_server
