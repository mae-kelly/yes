# L2 Arbitrage Scanner - Flash Loan Edition

Ultra-fast arbitrage scanner for Arbitrum L2 with flash loan execution.

## Features

- ⚡ Scans ALL L2 DEX pairs (10+ protocols)
- 💰 Automatic flash loan execution via Aave
- 🎯 Mempool monitoring for front-running protection
- 📊 Real-time profit calculations
- 🔍 Discovers new pairs automatically
- 🚀 Sub-100ms scanning speed

## Quick Start

1. Setup the scanner:
```bash
./setup.sh
```

2. Deploy the smart contract:
```bash
./deploy_contract.sh
```

3. Configure your RPC endpoints in `main.rs`

4. Run the scanner:
```bash
./run.sh
```

## Monitored DEXes

- UniswapV3
- SushiSwap
- Camelot
- TraderJoe
- Balancer
- Zyber
- Arbidex
- WooFi
- Ramses
- Chronos

## Configuration

Edit `config/dexes.json` to add more DEXes or modify parameters.

## Performance Optimization

- Parallel scanning of all pairs
- Batch RPC calls
- Memory-efficient data structures
- Optimized gas estimation

## Safety

- Always simulate transactions before execution
- Set minimum profit thresholds
- Monitor gas prices
- Use flashloan for capital efficiency

## License

MIT