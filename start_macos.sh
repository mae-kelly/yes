#!/bin/bash

# MacOS-compatible launcher for Scherman Trading System

set -e

echo "🚀 SCHERMAN TRADING SYSTEM - MACOS LAUNCHER"
echo "==========================================="

# Activate virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [ -d "venv" ]; then
        echo "⚡ Activating virtual environment..."
        source venv/bin/activate
    else
        echo "❌ No virtual environment found"
        exit 1
    fi
fi

# Check credentials
echo "🔐 Checking credentials..."
if [ ! -f ".env" ]; then
    echo "❌ No .env file found"
    echo "Run: ./setup_credentials.sh"
    exit 1
fi

if grep -q "your_okx_api_key_here" .env; then
    echo "❌ Credentials not configured"
    echo "Please edit .env with your real OKX API credentials"
    echo "Run: ./setup_credentials.sh"
    exit 1
fi

echo "✅ Credentials configured"

# Run health check
echo "🏥 Running health check..."
if ./health_check.sh; then
    echo "✅ Health check passed"
else
    echo "⚠️ Health check issues detected, but continuing..."
fi

# Simple system test
echo "🧪 Running system test..."
if python3 test_system_simple.py; then
    echo "✅ System test passed"
else
    echo "❌ System test failed"
    exit 1
fi

# Final confirmation
echo ""
echo "System appears ready. Continue? (y/n)"
read -r response

if [ "$response" != "y" ]; then
    echo "Launch cancelled"
    exit 0
fi

# Launch main system
echo "🎯 Starting trading system..."
python3 -c "
import sys
sys.path.insert(0, 'src')

# Import main components
try:
    from core.data_manager import EnterpriseDataManager
    from core.signal_engine import SchermanVIXDivergenceCore
    from core.risk_manager import RiskManager
    
    print('✅ All components loaded successfully')
    print('🎉 System is running!')
    print('📝 This is a basic launch - full trading system needs additional setup')
    print('⚠️ Always start with sandbox mode and small amounts')
    
except Exception as e:
    print(f'❌ Launch failed: {e}')
    sys.exit(1)
"
