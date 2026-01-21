#!/bin/bash
# Quick start script for MCP server with virtual environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Xray Deployment MCP Server - Quick Start"

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

# Start MCP server
echo "🚀 Starting MCP server..."
echo "📡 Ready for Open WebUI, Dify, or MCP clients"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python server.py
