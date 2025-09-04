#!/bin/bash

# create_all_files.sh
# This script creates all the necessary files for the arbitrage scanner

echo "🚀 Creating all files for L2 Arbitrage Scanner..."

# Create main.rs
cat > rust-engine/src/main.rs << 'EOF'
use ethers::prelude::*;
use std::sync::Arc;
use tokio::time::{Duration, interval};
use dashmap::DashMap;

mod scanner;
mod flash_loan;
mod mempool;
mod simulator;
mod pair_finder;
mod types;
mod utils;

use crate::scanner::PairScanner;
use crate::flash_loan::FlashLoanExecutor;
use crate::mempool::MempoolMonitor;
use crate::pair_finder::PairFinder;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🚀 L2 ARBITRAGE SCANNER - FLASH LOAN EDITION\n");
    println!("Scanning ALL L2 pairs with minimal competition...\n");
    
    // Multiple RPC endpoints for redundancy
    let rpcs = vec![
        "https://arb-mainnet.g.alchemy.com/v2/alcht_oZ7wU7JpIoZejlOWUcMFOpNsIlLDsX",
        "https://arbitrum-mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
        "https://rpc.ankr.com/arbitrum",
    ];
    
    let provider = Arc::new(Provider::<Http>::try_from(rpcs[0])?);
    
    // For now, use HTTP provider for both until WS is set up
    let ws_provider = provider.clone();
    
    // Initialize components
    let pair_finder = Arc::new(PairFinder::new(provider.clone()));
    let scanner = Arc::new(PairScanner::new(provider.clone()));
    let flash_executor = Arc::new(FlashLoanExecutor::new(provider.clone()));
    let mempool_monitor = Arc::new(MempoolMonitor::new(ws_provider.clone()));
    
    // Discover ALL pairs on L2
    println!("📊 Discovering all L2 pairs...");
    let all_pairs = pair_finder.discover_all_pairs().await?;
    println!("✅ Found {} total pairs to monitor\n", all_pairs.len());
    
    // Store opportunities
    let opportunities: Arc<DashMap<String, f64>> = Arc::new(DashMap::new());
    
    // Main scanning loop
    let mut interval = interval(Duration::from_millis(100)); // Ultra-fast scanning
    
    loop {
        interval.tick().await;
        
        // Scan all pairs in parallel batches
        let batch_size = 50;
        for chunk in all_pairs.chunks(batch_size) {
            let mut handles = vec![];
            
            for pair_set in chunk {
                let scanner = scanner.clone();
                let executor = flash_executor.clone();
                let pair_set = pair_set.clone();
                
                let handle = tokio::spawn(async move {
                    if let Some(opp) = scanner.scan_pair_set(&pair_set).await {
                        if opp.profit_after_gas > 50.0 { // $50 minimum profit
                            println!("💰 OPPORTUNITY FOUND!");
                            println!("   Tokens: {:?} <-> {:?}", opp.token0, opp.token1);
                            println!("   DEXs: {} -> {}", opp.buy_dex, opp.sell_dex);
                            println!("   Spread: {:.3}%", opp.spread);
                            println!("   Profit: ${:.2} (after gas)", opp.profit_after_gas);
                            println!("   Flash Loan: ${:.2}", opp.optimal_loan);
                            
                            // Execute with flash loan
                            if let Err(e) = executor.execute_arbitrage(&opp).await {
                                println!("   ⚠️ Execution failed: {}", e);
                            } else {
                                println!("   ✅ EXECUTED SUCCESSFULLY!");
                            }
                        }
                    }
                });
                
                handles.push(handle);
            }
            
            futures::future::join_all(handles).await;
        }
    }
}
EOF

# Create types.rs
cat > rust-engine/src/types.rs << 'EOF'
use ethers::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Opportunity {
    pub token0: Address,
    pub token1: Address,
    pub buy_dex: String,
    pub sell_dex: String,
    pub buy_pair: Address,
    pub sell_pair: Address,
    pub spread: f64,
    pub optimal_loan: f64,
    pub profit_after_gas: f64,
    pub gas_estimate: U256,
    pub block_number: u64,
}

#[derive(Clone, Debug)]
pub struct PairSet {
    pub token0: Address,
    pub token1: Address,
    pub dexes: Vec<DexPair>,
}

#[derive(Clone, Debug)]
pub struct DexPair {
    pub name: String,
    pub factory: Address,
    pub pair_address: Address,
    pub router: Address,
}

#[derive(Debug)]
pub struct FlashLoanParams {
    pub token: Address,
    pub amount: U256,
    pub target_contract: Address,
    pub callback_data: Bytes,
}
EOF

# Create scanner.rs
cat > rust-engine/src/scanner.rs << 'EOF'
use ethers::prelude::*;
use std::sync::Arc;
use crate::types::{Opportunity, PairSet, DexPair};

pub struct PairScanner {
    provider: Arc<Provider<Http>>,
    pair_abi: Abi,
}

impl PairScanner {
    pub fn new(provider: Arc<Provider<Http>>) -> Self {
        let pair_abi = ethers::abi::parse_abi(&[
            "function getReserves() view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)",
            "function token0() view returns (address)",
            "function token1() view returns (address)",
        ]).unwrap();
        
        Self {
            provider,
            pair_abi,
        }
    }
    
    pub async fn scan_pair_set(&self, pair_set: &PairSet) -> Option<Opportunity> {
        if pair_set.dexes.len() < 2 {
            return None;
        }
        
        // Get reserves for all DEXes in parallel
        let mut handles = vec![];
        for dex in &pair_set.dexes {
            let provider = self.provider.clone();
            let pair_abi = self.pair_abi.clone();
            let pair_addr = dex.pair_address;
            
            let handle = tokio::spawn(async move {
                let pair = Contract::new(pair_addr, pair_abi, provider);
                pair.method::<_, (U256, U256, U256)>("getReserves", ())
                    .unwrap()
                    .call()
                    .await
            });
            handles.push(handle);
        }
        
        let results = futures::future::join_all(handles).await;
        
        // Find best arbitrage opportunity
        let mut best_opportunity: Option<Opportunity> = None;
        let mut max_profit = 0.0;
        
        for (i, buy_result) in results.iter().enumerate() {
            if let Ok(Ok((buy_r0, buy_r1, _))) = buy_result {
                for (j, sell_result) in results.iter().enumerate() {
                    if i == j { continue; }
                    
                    if let Ok(Ok((sell_r0, sell_r1, _))) = sell_result {
                        // Calculate prices and spread
                        let buy_price = buy_r1.as_u128() as f64 / buy_r0.as_u128().max(1) as f64;
                        let sell_price = sell_r1.as_u128() as f64 / sell_r0.as_u128().max(1) as f64;
                        
                        let spread = ((sell_price - buy_price) / buy_price) * 100.0;
                        
                        if spread > 0.3 { // 0.3% minimum spread
                            // Calculate optimal flash loan amount
                            let optimal_loan = self.calculate_optimal_loan(
                                buy_r0.as_u128() as f64,
                                buy_r1.as_u128() as f64,
                                sell_r0.as_u128() as f64,
                                sell_r1.as_u128() as f64,
                            );
                            
                            // Estimate gas and profit
                            let gas_price = self.provider.get_gas_price().await.unwrap_or(U256::from(100_000_000)); // 0.1 gwei default
                            let gas_estimate = U256::from(500_000); // Conservative estimate
                            let gas_cost = (gas_price * gas_estimate).as_u128() as f64 / 1e18;
                            
                            let gross_profit = optimal_loan * spread / 100.0;
                            let flash_loan_fee = optimal_loan * 0.0009; // 0.09% Aave fee
                            let profit_after_gas = gross_profit - gas_cost - flash_loan_fee;
                            
                            if profit_after_gas > max_profit {
                                max_profit = profit_after_gas;
                                best_opportunity = Some(Opportunity {
                                    token0: pair_set.token0,
                                    token1: pair_set.token1,
                                    buy_dex: pair_set.dexes[i].name.clone(),
                                    sell_dex: pair_set.dexes[j].name.clone(),
                                    buy_pair: pair_set.dexes[i].pair_address,
                                    sell_pair: pair_set.dexes[j].pair_address,
                                    spread,
                                    optimal_loan,
                                    profit_after_gas,
                                    gas_estimate,
                                    block_number: self.provider.get_block_number().await.unwrap_or_default().as_u64(),
                                });
                            }
                        }
                    }
                }
            }
        }
        
        best_opportunity
    }
    
    fn calculate_optimal_loan(&self, r0_buy: f64, r1_buy: f64, r0_sell: f64, r1_sell: f64) -> f64 {
        // Simplified optimal arbitrage calculation
        let k_buy = r0_buy * r1_buy;
        let k_sell = r0_sell * r1_sell;
        
        // Calculate optimal input amount
        let optimal = ((k_buy * k_sell).sqrt() - k_buy) / 997.0 * 1000.0;
        
        optimal.max(1000.0).min(1_000_000.0) // Between $1k and $1M
    }
}
EOF

# Create flash_loan.rs
cat > rust-engine/src/flash_loan.rs << 'EOF'
use ethers::prelude::*;
use std::sync::Arc;
use crate::types::{Opportunity, FlashLoanParams};

pub struct FlashLoanExecutor {
    provider: Arc<Provider<Http>>,
    aave_pool: Address,
    executor_contract: Address,
}

impl FlashLoanExecutor {
    pub fn new(provider: Arc<Provider<Http>>) -> Self {
        Self {
            provider,
            aave_pool: "0x794a61358D6845594F94dc1DB02A252b5b4814aD".parse().unwrap(), // Aave V3 Pool
            executor_contract: "0x0000000000000000000000000000000000000000".parse().unwrap(), // Deploy your contract
        }
    }
    
    pub async fn execute_arbitrage(&self, opportunity: &Opportunity) -> Result<(), Box<dyn std::error::Error>> {
        // Build flash loan execution calldata
        let flash_loan_abi = ethers::abi::parse_abi(&[
            "function flashLoanSimple(address receiver, address asset, uint256 amount, bytes calldata params, uint16 referralCode) external",
        ])?;
        
        // Encode arbitrage parameters for callback
        let callback_data = ethers::abi::encode(&[
            Token::Address(opportunity.buy_pair),
            Token::Address(opportunity.sell_pair),
            Token::Uint(U256::from_f64_lossy(opportunity.optimal_loan)),
        ]);
        
        let aave = Contract::new(self.aave_pool, flash_loan_abi, self.provider.clone());
        
        // Execute flash loan
        let tx = aave
            .method::<_, ()>(
                "flashLoanSimple",
                (
                    self.executor_contract,
                    opportunity.token0,
                    U256::from_f64_lossy(opportunity.optimal_loan),
                    Bytes::from(callback_data),
                    0u16,
                ),
            )?
            .gas(opportunity.gas_estimate)
            .send()
            .await?;
        
        println!("   📝 Transaction: {:?}", tx.tx_hash());
        
        // Wait for confirmation
        let receipt = tx.await?;
        
        if let Some(receipt) = receipt {
            if receipt.status == Some(U64::from(1)) {
                println!("   ✅ Success! Gas used: {}", receipt.gas_used.unwrap_or_default());
                return Ok(());
            }
        }
        
        Err("Transaction failed".into())
    }
}
EOF

# Create pair_finder.rs
cat > rust-engine/src/pair_finder.rs << 'EOF'
use ethers::prelude::*;
use std::sync::Arc;
use std::collections::HashSet;
use crate::types::{PairSet, DexPair};

pub struct PairFinder {
    provider: Arc<Provider<Http>>,
    factories: Vec<(String, Address, Address)>, // (name, factory, router)
}

impl PairFinder {
    pub fn new(provider: Arc<Provider<Http>>) -> Self {
        Self {
            provider,
            factories: vec![
                // Major DEXes on Arbitrum
                ("UniswapV3", "0x1F98431c8aD98523631AE4a59f267346ea31F984".parse().unwrap(), 
                 "0xE592427A0AEce92De3Edee1F18E0157C05861564".parse().unwrap()),
                ("SushiSwap", "0xc35DADB65012eC5796536bD9864eD8773aBc74C4".parse().unwrap(),
                 "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506".parse().unwrap()),
                ("Camelot", "0x6EcCab422D763aC031210895C81787E87B43A652".parse().unwrap(),
                 "0xc873fEcbd354f5A56E00E710B90EF4201db2448d".parse().unwrap()),
            ],
        }
    }
    
    pub async fn discover_all_pairs(&self) -> Result<Vec<PairSet>, Box<dyn std::error::Error>> {
        let factory_abi = ethers::abi::parse_abi(&[
            "function allPairsLength() view returns (uint256)",
            "function allPairs(uint256) view returns (address)",
            "function getPair(address, address) view returns (address)",
        ])?;
        
        let mut all_pair_sets: Vec<PairSet> = Vec::new();
        let mut token_pairs: HashSet<(Address, Address)> = HashSet::new();
        
        // For testing, just create some known pairs
        let test_pairs = vec![
            // WETH/USDC
            ("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1".parse()?, 
             "0xaf88d065e77c8cC2239327C5EDb3A432268e5831".parse()?),
            // WETH/ARB
            ("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1".parse()?, 
             "0x912CE59144191C1204E64559FE8253a0e49E6548".parse()?),
        ];
        
        for (token0, token1) in test_pairs {
            let mut dexes = Vec::new();
            
            for (dex_name, factory_addr, router_addr) in &self.factories {
                // For testing, assume all pairs exist on all DEXes
                dexes.push(DexPair {
                    name: dex_name.clone(),
                    factory: *factory_addr,
                    pair_address: *factory_addr, // Using factory as placeholder
                    router: *router_addr,
                });
            }
            
            if dexes.len() >= 2 {
                all_pair_sets.push(PairSet {
                    token0,
                    token1,
                    dexes,
                });
            }
        }
        
        Ok(all_pair_sets)
    }
}
EOF

# Create mempool.rs
cat > rust-engine/src/mempool.rs << 'EOF'
use ethers::prelude::*;
use std::sync::Arc;
use dashmap::DashMap;

pub struct MempoolMonitor {
    provider: Arc<Provider<Http>>,
}

impl MempoolMonitor {
    pub fn new(provider: Arc<Provider<Http>>) -> Self {
        Self { provider }
    }
    
    pub async fn watch_for_opportunities(&self, opportunities: Arc<DashMap<String, f64>>) {
        // Simplified version for HTTP provider
        loop {
            if let Ok(block_number) = self.provider.get_block_number().await {
                println!("Monitoring block: {}", block_number);
            }
            tokio::time::sleep(tokio::time::Duration::from_secs(5)).await;
        }
    }
}
EOF

# Create simulator.rs
cat > rust-engine/src/simulator.rs << 'EOF'
use ethers::prelude::*;
use std::sync::Arc;

pub struct Simulator {
    provider: Arc<Provider<Http>>,
}

impl Simulator {
    pub fn new(provider: Arc<Provider<Http>>) -> Self {
        Self { provider }
    }
    
    pub async fn simulate_arbitrage(&self, opportunity: &crate::types::Opportunity) -> Result<bool, Box<dyn std::error::Error>> {
        // Use eth_call to simulate the transaction
        let call_data = self.build_arbitrage_calldata(opportunity)?;
        
        let tx = TransactionRequest::new()
            .to(opportunity.buy_pair)
            .data(call_data)
            .gas(opportunity.gas_estimate);
        
        match self.provider.call(&tx.into(), None).await {
            Ok(_) => Ok(true),
            Err(_) => Ok(false),
        }
    }
    
    fn build_arbitrage_calldata(&self, opportunity: &crate::types::Opportunity) -> Result<Bytes, Box<dyn std::error::Error>> {
        // Build the calldata for the arbitrage execution
        let swap_abi = ethers::abi::parse_abi(&[
            "function swap(uint256 amount0Out, uint256 amount1Out, address to, bytes calldata data)",
        ])?;
        
        let swap = swap_abi.function("swap")?;
        let encoded = swap.encode_input(&[
            Token::Uint(U256::from_f64_lossy(opportunity.optimal_loan)),
            Token::Uint(U256::zero()),
            Token::Address(opportunity.sell_pair),
            Token::Bytes(vec![]),
        ])?;
        
        Ok(encoded.into())
    }
}
EOF

# Create utils.rs
cat > rust-engine/src/utils.rs << 'EOF'
use ethers::prelude::*;

pub fn calculate_profit_after_fees(
    input_amount: f64,
    price_diff: f64,
    gas_cost: f64,
    flash_loan_fee: f64,
) -> f64 {
    let gross_profit = input_amount * price_diff;
    let total_fees = gas_cost + (input_amount * flash_loan_fee);
    gross_profit - total_fees
}

pub fn format_token_amount(amount: U256, decimals: u8) -> String {
    let divisor = U256::exp10(decimals as usize);
    let whole = amount / divisor;
    let remainder = amount % divisor;
    
    format!("{}.{:0>width$}", whole, remainder, width = decimals as usize)
}

pub fn estimate_gas_cost(gas_price: U256, gas_units: u64) -> f64 {
    (gas_price.as_u128() as f64 * gas_units as f64) / 1e18
}
EOF

# Update Cargo.toml with proper dependencies
cat > rust-engine/Cargo.toml << 'EOF'
[package]
name = "arb-scanner"
version = "0.2.0"
edition = "2021"

[dependencies]
ethers = "2.0"
tokio = { version = "1", features = ["full"] }
tokio-stream = "0.1"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
dashmap = "6.1"
parking_lot = "0.12"
chrono = "0.4"
futures = "0.3"
hex = "0.4"

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
strip = false
EOF

echo "✅ All files created successfully!"
echo ""
echo "Now rebuilding the project..."
cd rust-engine
cargo build --release

echo ""
echo "✅ Setup complete! Run with: ./run.sh"
EOF

chmod +x create_all_files.sh
./create_all_files.sh