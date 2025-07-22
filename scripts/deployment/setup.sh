#!/bin/bash
set -e

echo "🚀 PERFECT ENVIRONMENT SETUP"
echo "============================="

echo "🐍 Checking Python version..."
python3_version=$(python3 --version 2>&1 | cut -d' ' -f2)
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "✅ Python $python3_version is suitable"
else
    echo "❌ Python 3.8+ required, found $python3_version"
    exit 1
fi

echo "🏗️ Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo "⚡ Activating virtual environment..."
source venv/bin/activate

echo "📦 Upgrading pip..."
pip install --upgrade pip --quiet

echo "📚 Installing dependencies..."
pip install --upgrade ccxt>=4.1.0 --quiet
pip install --upgrade pandas>=2.0.0 --quiet  
pip install --upgrade numpy>=1.24.0 --quiet
pip install --upgrade requests>=2.28.0 --quiet
pip install --upgrade python-dotenv>=1.0.0 --quiet
pip install --upgrade aiohttp>=3.8.0 --quiet
pip install --upgrade asyncio-throttle>=1.0.0 --quiet
pip install --upgrade websockets>=11.0 --quiet

echo "✅ All dependencies installed successfully"

echo "🔧 Creating environment configuration..."
cat > .env << 'ENVFILE'
TRADING_MODE=sandbox
LOG_LEVEL=INFO
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_HEALTH_CHECKS=true
DEFAULT_RISK_PER_TRADE=0.01
DEFAULT_MAX_PORTFOLIO_HEAT=0.05
DEFAULT_MIN_CONFIDENCE=0.70
ENABLE_CACHING=true
ENABLE_PARALLEL_PROCESSING=true
API_TIMEOUT=30
MAX_API_RETRIES=3
ENVFILE

echo "✅ Environment configuration created"

echo "📁 Creating directories..."
mkdir -p logs data
chmod 700 logs data
chmod 600 .env
echo "✅ Secure directories created"

echo "🚀 Creating launcher script..."
cat > launch_perfect_system.sh << 'LAUNCHER'
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
LAUNCHER

chmod +x launch_perfect_system.sh
echo "✅ Launcher script created"

python3 -c "
try:
    import ccxt, pandas, numpy, requests
    print('✅ Core libraries working')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

if [ -r .env ] && [ -w logs ] && [ -w data ]; then
    echo "✅ File permissions correct"
else
    echo "❌ File permission issues"
    exit 1
fi

echo ""
echo "🎉 PERFECT ENVIRONMENT SETUP COMPLETE!"
echo "======================================"
echo "✅ Virtual environment: Ready"
echo "✅ Dependencies: Installed"
echo "✅ Configuration: Created"
echo "✅ Security: Configured"
echo "✅ Logging: Enabled"
echo "✅ Performance: Optimized"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. ./launch_perfect_system.sh"
echo "2. Start with sandbox mode"
echo "3. Monitor for 24 hours"
echo "4. Scale gradually"
echo ""
echo "🏆 READY FOR PERFECT TRADING!"
