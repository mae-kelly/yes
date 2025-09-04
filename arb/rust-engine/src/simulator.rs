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
