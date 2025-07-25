# Scherman VIX Divergence Trading System

A clean, focused implementation of VIX divergence trading methodology for cryptocurrency markets.

## Quick Start

1. **Test the System**
   ```bash
   ./scripts/test.sh
   ```

2. **Configure Your Credentials**
   ```bash
   cp .env.template .env
   ```

3. **Run the Trading System**
   ```bash
   ./scripts/run.sh
   ```

## Key Features

- Clean Implementation: No unnecessary complexity or broken features
- Real Methodology: Based on proven VIX divergence principles
- Risk Management: Built-in position sizing and risk controls  
- Paper Trading: Test safely before using real money
- Live Data: Uses real market data and sentiment indicators

## Important Notes

- Always start in sandbox mode (default)
- Never risk more than you can afford to lose
- Test thoroughly before live trading
- This is educational software - trade at your own risk

## File Structure

```
├── core/                 # Core trading logic
│   ├── scherman_vix.py  # Main methodology
│   ├── data_manager.py  # Data management
│   └── trader.py        # Trading system
├── config/              # Configuration
├── scripts/             # Utility scripts
└── logs/               # Trading logs
```

## Risk Warning

Cryptocurrency trading involves substantial risk of loss. This software is provided for educational purposes. Always conduct thorough testing and never invest more than you can afford to lose.
