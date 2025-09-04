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
