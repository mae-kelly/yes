#!/bin/bash
# AO1 Log Visibility Dashboard - Client Startup Script

echo "Starting AO1 Log Visibility Measurement Dashboard Client"
echo "========================================================"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install npm."
    exit 1
fi

# Navigate to client directory
cd client

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Check if server is running
echo "Checking if server is running on http://localhost:5000..."
if ! curl -s http://localhost:5000/api/global-view > /dev/null; then
    echo ""
    echo "Warning: Server appears to be down"
    echo "Please start the server first by running: ./server.sh"
    echo "Then run this client script in a new terminal"
    echo ""
    echo "Starting client anyway (server must be started separately)..."
    echo ""
fi

# Start the development server
echo "Starting Vite development server..."
echo "Dashboard will be available at http://localhost:3000"
echo ""
echo "To stop the client, press Ctrl+C"
echo "========================================================"

npm run dev