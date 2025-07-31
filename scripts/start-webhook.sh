#!/bin/bash

# Start the webhook server
# Usage: ./scripts/start-webhook.sh [port] [debug]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
PORT=${1:-8080}
DEBUG=${2:-false}
HOST="0.0.0.0"

echo "🚀 Starting Wandr Webhook Service..."
echo "📍 Project root: $PROJECT_ROOT"
echo "🌐 Host: $HOST"
echo "🔌 Port: $PORT"
echo "🐛 Debug: $DEBUG"

# Change to project root
cd "$PROJECT_ROOT"

# Set environment variables
export HOST="$HOST"
export PORT="$PORT"
export DEBUG="$DEBUG"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found in project root"
    exit 1
fi

echo "✅ Starting Flask server..."
python app.py