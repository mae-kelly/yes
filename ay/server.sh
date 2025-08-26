#!/bin/bash
# AO1 Log Visibility Dashboard - Server Startup Script

echo "🚀 Starting AO1 Log Visibility Measurement Dashboard Server"
echo "=========================================================="

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python3; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Check current directory
echo "📍 Current directory: $(pwd)"
echo "📁 Contents: $(ls -la)"

# Check if database file exists
if [ ! -f "universal_cmdb.db" ]; then
    echo "⚠️  WARNING: universal_cmdb.db not found in current directory"
    echo "Looking for database file in other locations..."
    
    # Search for the database file
    DB_LOCATIONS=(
        "./universal_cmdb.db"
        "../universal_cmdb.db"
        "./server/universal_cmdb.db"
        "$HOME/universal_cmdb.db"
    )
    
    DB_FOUND=false
    for db_path in "${DB_LOCATIONS[@]}"; do
        if [ -f "$db_path" ]; then
            echo "✅ Found database at: $db_path"
            # Create symlink if not in current directory
            if [ "$db_path" != "./universal_cmdb.db" ]; then
                ln -sf "$db_path" "./universal_cmdb.db"
                echo "🔗 Created symlink to database"
            fi
            DB_FOUND=true
            break
        fi
    done
    
    if [ "$DB_FOUND" = false ]; then
        echo "❌ Database file 'universal_cmdb.db' not found!"
        echo "Please ensure your database file is accessible from the project root"
        echo "Continuing anyway for testing with stub data..."
    fi
else
    echo "✅ Database file found: universal_cmdb.db"
    echo "📊 Database size: $(du -h universal_cmdb.db | cut -f1)"
fi

# Navigate to server directory
cd server || {
    echo "❌ Server directory not found!"
    exit 1
}

echo "📁 Server directory contents: $(ls -la)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv || {
        echo "❌ Failed to create virtual environment"
        exit 1
    }
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate || {
    echo "❌ Failed to activate virtual environment"
    exit 1
}

echo "✅ Virtual environment activated"
echo "🐍 Python path: $(which python)"
echo "🐍 Pip path: $(which pip)"

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt || {
    echo "❌ Failed to install dependencies"
    echo "📋 Requirements file contents:"
    cat requirements.txt
    exit 1
}

echo "✅ Dependencies installed"
echo "📦 Installed packages:"
pip list

# Check if DuckDB is accessible
echo "🦆 Testing DuckDB installation..."
python3 -c "
import duckdb
import sys
import os
print('✅ DuckDB version:', duckdb.__version__)
print('✅ DuckDB is available')

# Test database connection
db_path = '../universal_cmdb.db'
if os.path.exists(db_path):
    try:
        conn = duckdb.connect(db_path)
        tables = conn.execute('SHOW TABLES').fetchall()
        print(f'✅ Database connected, tables: {tables}')
        if ('universal_cmdb',) in tables:
            count = conn.execute('SELECT COUNT(*) FROM universal_cmdb').fetchone()[0]
            print(f'✅ universal_cmdb table has {count} rows')
        conn.close()
    except Exception as e:
        print(f'⚠️ Database connection failed: {e}')
else:
    print('⚠️ Database file not found, using stub data')
" || {
    echo "❌ DuckDB test failed"
    exit 1
}

# Test Flask import
echo "🌐 Testing Flask installation..."
python3 -c "
import flask
from flask_cors import CORS
print('✅ Flask version:', flask.__version__)
print('✅ Flask and CORS available')
" || {
    echo "❌ Flask test failed"
    exit 1
}

# Check if port 5000 is available
echo "🔌 Checking if port 5000 is available..."
if lsof -i :5000 >/dev/null 2>&1; then
    echo "⚠️  Port 5000 is already in use"
    echo "🔍 Process using port 5000:"
    lsof -i :5000
    echo ""
    read -p "Kill existing process? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo lsof -ti:5000 | xargs kill -9
        echo "✅ Port 5000 freed"
    else
        echo "⚠️ Starting server anyway (may fail)"
    fi
else
    echo "✅ Port 5000 is available"
fi

# Start the Flask server with detailed logging
echo ""
echo "🌐 Starting Flask server on http://localhost:5000"
echo "📊 API endpoints will be available at http://localhost:5000/api/"
echo "🔍 Debug endpoint: http://localhost:5000/api/health"
echo "🔍 Database info: http://localhost:5000/api/debug/columns"
echo ""
echo "📝 Server logs will be written to server_debug.log"
echo "To stop the server, press Ctrl+C"
echo "=========================================================="

export FLASK_ENV=development
export FLASK_DEBUG=1

# Start with error handling
python3 app.py 2>&1 | tee server_debug.log