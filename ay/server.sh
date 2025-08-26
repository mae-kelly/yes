#!/bin/bash
# AO1 Log Visibility Dashboard - Server Startup Script

echo "🚀 Starting AO1 Log Visibility Measurement Dashboard Server"
echo "=========================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if database file exists
if [ ! -f "universal_cmdb.db" ]; then
    echo "⚠️  Warning: universal_cmdb.db not found in current directory"
    echo "Please ensure your database file is in the project root"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "server/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd server
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source server/venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
cd server
pip install -r requirements.txt

# Check if DuckDB is accessible
python3 -c "import duckdb; print('✅ DuckDB is available')" || {
    echo "❌ DuckDB installation failed"
    exit 1
}

# Start the Flask server
echo "🌐 Starting Flask server on http://localhost:5000"
echo "📊 API endpoints will be available at http://localhost:5000/api/"
echo ""
echo "To stop the server, press Ctrl+C"
echo "=========================================================="

export FLASK_ENV=development
python3 app.py