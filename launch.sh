#!/bin/bash

echo "🚀 SCHERMAN CRYPTO STRATEGY LAUNCHER"
echo "=================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if required packages are installed
echo "🔍 Checking dependencies..."
python3 -c "import ccxt, pandas, numpy" 2>/dev/null || {
    echo "⚠️  Installing required packages..."
    pip3 install -r requirements.txt
}

# Run system test
echo "🧪 Running system test..."
python3 test_system.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ System test passed!"
    echo ""
    echo "🎯 Starting Scherman Crypto Strategy..."
    echo ""
    python3 main.py
else
    echo "❌ System test failed - please check your installation"
    exit 1
fi
