#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting L2 Arbitrage Scanner${NC}"
echo ""

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo -e "${RED}Error: Rust is not installed${NC}"
    echo "Install from: https://rustup.rs/"
    exit 1
fi

# Check if binary exists
if [ ! -f "rust-engine/target/release/arb-scanner" ]; then
    echo -e "${YELLOW}Binary not found. Building...${NC}"
    cd rust-engine
    cargo build --release
    cd ..
fi

# Create log file with timestamp
LOG_FILE="logs/arb_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

echo -e "${GREEN}Starting scanner...${NC}"
echo "Logs will be saved to: $LOG_FILE"
echo ""

# Run with environment variables
export RUST_LOG=info
export RUST_BACKTRACE=1

# Run the scanner with logging
rust-engine/target/release/arb-scanner 2>&1 | tee "$LOG_FILE"
