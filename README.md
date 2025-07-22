# Scherman Crypto Trading System - Production Ready

[![Security](https://img.shields.io/badge/Security-Hardened-green.svg)](docs/security.md)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](docs/deployment.md)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](tests/)

## 🏆 Professional Cryptocurrency Trading System

Advanced, secure, and compliant cryptocurrency trading system implementing the Scherman VIX Divergence methodology with enterprise-grade security and monitoring.

## ⚡ Quick Start (Production)

### Prerequisites
- Python 3.8+
- 8GB+ RAM
- Linux/MacOS (Ubuntu 20.04+ recommended)
- Valid exchange API keys

### 1. Environment Setup
```bash
# Clone and enter directory
git clone <repository> && cd scherman-crypto-system

# Run production setup
./scripts/deployment/setup.sh

# Configure environment (REQUIRED)
cp config/environments/.env.template .env
# Edit .env with your actual API keys and configuration
```

### 2. Security Configuration
```bash
# Generate encryption keys
openssl rand -base64 32 > config/encryption.key
chmod 600 config/encryption.key

# Set secure permissions
chmod 700 logs data config
chmod 600 .env
```

### 3. Launch System
```bash
# Production launch (sandbox mode)
./scripts/deployment/launch_system.sh

# For live trading (after thorough testing)
TRADING_MODE=live ./scripts/deployment/launch_system.sh
```

## 🛡️ Security Features

- ✅ **Zero Hardcoded Credentials** - All secrets in environment variables
- ✅ **Input Validation** - Comprehensive validation of all inputs  
- ✅ **Audit Logging** - Tamper-evident audit trail
- ✅ **Rate Limiting** - API protection and abuse prevention
- ✅ **Encryption** - Data at rest and in transit
- ✅ **Monitoring** - Real-time security monitoring
- ✅ **Backup System** - Automated encrypted backups

## 📊 System Architecture

```
src/
├── core/           # Core trading system
├── security/       # Security modules
├── api/           # API endpoints
└── utils/         # Utility functions

config/
├── environments/   # Environment configurations
└── templates/     # Configuration templates

logs/
├── trading/       # Trading logs
├── security/      # Security events
├── system/        # System logs
└── audit/         # Audit trail

monitoring/
├── dashboards/    # Grafana dashboards
├── alerts/        # Alert configurations
└── metrics/       # Custom metrics
```

## 🔧 Configuration

### Required Environment Variables

```bash
# Exchange API (Required)
OKX_API_KEY=your_key_here
OKX_SECRET=your_secret_here  
OKX_PASSPHRASE=your_passphrase_here

# Trading Configuration
TRADING_MODE=sandbox          # sandbox or live
DEFAULT_RISK_PER_TRADE=0.01  # 1% risk per trade
MAX_PORTFOLIO_HEAT=0.05      # 5% max portfolio risk

# Security
ENCRYPTION_KEY=your_encryption_key_here
SESSION_SECRET=your_session_secret_here
```

See [config/environments/.env.template](config/environments/.env.template) for full configuration.

## 📈 Trading Features

- **VIX Divergence Signals** - Advanced fear/greed analysis
- **Multi-Asset Support** - BTC, ETH, and major altcoins
- **Risk Management** - Dynamic position sizing and risk controls
- **Execution Algorithms** - TWAP, VWAP, Iceberg, and smart routing
- **Portfolio Management** - Real-time P&L and performance tracking
- **ML Integration** - Machine learning enhanced signals

## 🚨 Production Checklist

Before going live, ensure:

- [ ] All environment variables configured
- [ ] API keys tested and working
- [ ] Backup system tested
- [ ] Monitoring dashboards configured
- [ ] Alert notifications working
- [ ] Security audit completed
- [ ] Compliance requirements met
- [ ] Disaster recovery plan tested

## 📋 Monitoring

Access monitoring at:
- **Metrics**: http://localhost:9090 (Prometheus)
- **Dashboards**: http://localhost:3000 (Grafana)
- **Health**: http://localhost:8080/health
- **Logs**: `logs/` directory

## 🔐 Security Best Practices

1. **Never commit secrets** to version control
2. **Use strong passwords** and API keys
3. **Enable 2FA** on all exchange accounts
4. **Regular backups** with encryption
5. **Monitor logs** for suspicious activity
6. **Keep software updated**
7. **Use hardware wallets** for cold storage

## 🆘 Support & Troubleshooting

### Common Issues

**API Connection Errors**
```bash
# Check API credentials
grep -E "(API_KEY|SECRET|PASSPHRASE)" .env

# Test connection
python -c "from src.core.data_manager import *; test_connection()"
```

**Permission Errors**
```bash
# Fix permissions
chmod 700 logs data config
chmod 600 .env
```

### Logs
- System logs: `logs/system/`
- Trading logs: `logs/trading/`
- Security logs: `logs/security/`
- Audit logs: `logs/audit/`

## ⚖️ Legal Disclaimer

**RISK WARNING**: Cryptocurrency trading involves substantial risk of loss. Past performance does not guarantee future results. Only trade with capital you can afford to lose.

This software is provided "as is" without warranties. Users are responsible for:
- Compliance with local regulations
- Proper risk management
- Security of their accounts and funds
- All trading decisions and outcomes

## 📄 License

Copyright (c) 2025 Scherman Trading System. All rights reserved.

This software is licensed for production use. See LICENSE file for details.

---

**🛡️ Security Audited | 🏆 Production Ready | 📊 Enterprise Grade**

