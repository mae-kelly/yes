# Scherman Crypto Trading Strategy

A professional cryptocurrency trading system implementing Ivan Scherman's VIX divergence methodology with Renaissance Technologies-inspired machine learning integration.

## 🚀 Features

- **VIX Divergence Methodology**: Ivan Scherman's proven 75.3% win rate pattern recognition
- **Machine Learning Integration**: Renaissance Technologies-inspired ensemble models
- **Professional Risk Management**: Institutional-grade position sizing and portfolio protection
- **Real-time Data Feeds**: Fear & Greed Index, whale alerts, news sentiment, social sentiment
- **Advanced Execution**: TWAP, VWAP, Iceberg, and smart order routing algorithms
- **Live Trading Ready**: Production-grade system with comprehensive monitoring

## 📋 Requirements

- Python 3.8+
- OKX Exchange API access
- Minimum 10,000 USDT capital recommended
- Optional: Whale Alert, NewsAPI, LunarCrush API keys

## 🔧 Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd scherman-crypto-strategy
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the strategy:
```bash
python main.py
```

## ⚙️ Configuration

The system will prompt you for:
- OKX API credentials (API Key, Secret, Passphrase)
- Sandbox mode (recommended for testing)
- Optional alternative data API keys

## 🎯 Usage

1. **First Time Setup**:
   - Start with sandbox mode
   - Test with small amounts
   - Monitor performance closely

2. **Live Trading**:
   - Fund your OKX account
   - Enter live API credentials
   - Confirm live trading mode
   - Monitor system performance

## 📊 Strategy Overview

The system combines:
- **Scherman VIX Divergence** (70% weight): Market fear/greed divergence patterns
- **Renaissance ML Models** (30% weight): Ensemble machine learning predictions

### Signal Generation
1. VIX divergence detection using Fear & Greed Index
2. Machine learning ensemble predictions
3. Signal fusion with confidence weighting
4. Risk management validation
5. Position sizing optimization

### Risk Management
- Maximum 2% risk per trade
- 15% maximum portfolio heat
- Dynamic position sizing based on volatility
- Stop losses and take profits
- Drawdown protection

## 📈 Performance Monitoring

The system tracks:
- Real-time P&L
- Win rate and profit factor
- Maximum drawdown
- Sharpe ratio
- Portfolio heat and leverage

## ⚠️ Risk Warning

**IMPORTANT**: This is a live trading system that uses real money. Trading cryptocurrencies involves substantial risk of loss. Only trade with capital you can afford to lose.

- Start with sandbox mode
- Test thoroughly before live trading
- Use appropriate position sizing
- Monitor the system continuously
- Have stop-loss mechanisms in place

## 🔐 Security

- API keys are entered securely via getpass
- No hardcoded credentials
- Sandbox mode available for testing
- All sensitive data encrypted

## 📞 Support

For questions or issues:
1. Check the logs for error messages
2. Verify API credentials and permissions
3. Ensure sufficient account balance
4. Test in sandbox mode first

## 📄 License

This project is for educational and research purposes. Users are responsible for compliance with local regulations and exchange terms of service.

---

**Disclaimer**: Past performance does not guarantee future results. This system is provided as-is without warranties. Use at your own risk.
