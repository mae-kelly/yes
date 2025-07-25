#!/bin/bash

cd "$(dirname "$0")/.."

if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ ! -f "venv/.installed" ]; then
    echo "📦 Installing requirements..."
    pip install ccxt pandas numpy requests python-dotenv
    touch venv/.installed
fi

if [ ! -f ".env" ]; then
    echo "⚠️ No .env file found!"
    echo "Copy .env.template to .env and configure your API keys"
    exit 1
fi

set -a
source .env
set +a

echo "🎯 Starting Scherman Trading System..."
cd core
python3 trader.py
