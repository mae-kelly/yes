#!/bin/bash

echo "🚀 LAUNCHING SCHERMAN PERFECT TRADING SYSTEM"
echo "============================================="

if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚡ Activating virtual environment..."
    source venv/bin/activate
fi

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "🧪 Running system tests..."
python3 test_perfect_system.py

if [ $? -eq 0 ]; then
    echo "✅ All tests passed - starting trading system"
    python3 production_main.py
else
    echo "❌ Tests failed - please fix issues before running"
    exit 1
fi
