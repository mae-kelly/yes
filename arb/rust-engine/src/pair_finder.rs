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
