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
