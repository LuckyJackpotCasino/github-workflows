#!/bin/bash

# Start the BuildBot9000 Auto-Fix Agent

echo "🤖 Starting BuildBot9000 Auto-Fix Agent..."

cd "$(dirname "$0")"

# Kill any existing agent
pkill -f "python3 build-fix-agent.py" 2>/dev/null || true
sleep 1

# Start the agent in the background
nohup python3 build-fix-agent.py > /tmp/buildbot-agent.log 2>&1 &
AGENT_PID=$!

sleep 3

# Check if it started
if ps -p $AGENT_PID > /dev/null 2>&1; then
    echo "✅ Agent started successfully! (PID: $AGENT_PID)"
    echo "📋 Logs: tail -f /tmp/buildbot-agent.log"
else
    echo "❌ Failed to start agent"
    echo "Check logs: cat /tmp/buildbot-agent.log"
    exit 1
fi

