#!/bin/bash

# Production Safe Launcher - No shortcuts, all validations

set -e

echo "🚀 SCHERMAN CRYPTO SYSTEM - PRODUCTION LAUNCHER"
echo "==============================================="

# Pre-flight checks
echo "🔍 Running pre-flight checks..."

# 1. Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Python 3.8+ required, found $python_version"
    exit 1
fi
echo "✅ Python version: $python_version"

# 2. Check virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [ -d "venv" ]; then
        echo "⚡ Activating virtual environment..."
        source venv/bin/activate
    else
        echo "❌ No virtual environment found. Run setup first."
        exit 1
    fi
fi
echo "✅ Virtual environment active"

# 3. Validate credentials
echo "🔐 Validating credentials..."
if ! python3 validate_credentials.py; then
    exit 1
fi

# 4. Check required dependencies
echo "📦 Checking dependencies..."
python3 -c "import ccxt, pandas, numpy, requests" || {
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements.txt
}
echo "✅ Dependencies available"

# 5. Check system resources
echo "💻 Checking system resources..."
available_memory=$(free -m | awk 'NR==2{print $7}')
if [ "$available_memory" -lt 1000 ]; then
    echo "⚠️ Low memory: ${available_memory}MB available"
    echo "Continue anyway? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi
echo "✅ System resources adequate"

# 6. Final confirmation for live trading
if [ "${TRADING_MODE:-sandbox}" = "live" ]; then
    echo ""
    echo "🚨 LIVE TRADING MODE DETECTED"
    echo "⚠️  This will use REAL MONEY!"
    echo "⚠️  You can LOSE REAL MONEY!"
    echo ""
    echo "Type 'I_ACCEPT_ALL_RISKS' to proceed:"
    read -r confirmation
    
    if [ "$confirmation" != "I_ACCEPT_ALL_RISKS" ]; then
        echo "❌ Live trading cancelled"
        exit 1
    fi
    
    echo "🔴 LIVE TRADING CONFIRMED"
else
    echo "✅ Running in sandbox mode"
fi

# 7. Launch system
echo ""
echo "🎯 Starting Scherman Trading System..."
echo "Press Ctrl+C to stop"
echo ""

cd "$(dirname "${BASH_SOURCE[0]}")"
python3 -c "
import sys
sys.path.insert(0, 'src')
from core.main import main
main()
"
