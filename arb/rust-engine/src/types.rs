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
