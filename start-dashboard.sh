#!/bin/bash

echo "🎰 Starting Lucky Jackpot Casino Build Dashboard..."
echo ""

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Install it with: brew install python3"
    exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed!"
    echo "Install it with: brew install gh"
    exit 1
fi

# Check if gh is authenticated
if ! gh auth status &> /dev/null; then
    echo "⚠️  GitHub CLI is not authenticated"
    echo "Run: gh auth login"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Kill any existing server on port 9000
if lsof -ti :9000 &> /dev/null; then
    echo "🔄 Stopping existing server on port 9000..."
    lsof -ti :9000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Start the server
echo "🚀 Starting server on http://localhost:9000"
echo ""
echo "Dashboard Features:"
echo "  • Real-time build status for all 9 apps"
echo "  • Trigger builds with one click"
echo "  • Auto-refreshes every 30 seconds"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start server in background
python3 server.py &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

# Check if server started successfully
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server running (PID: $SERVER_PID)"
    
    # Open browser
    if command -v open &> /dev/null; then
        open http://localhost:9000
    else
        echo "📱 Open http://localhost:9000 in your browser"
    fi
    
    # Wait for server process
    wait $SERVER_PID
else
    echo "❌ Server failed to start"
    exit 1
fi
