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
