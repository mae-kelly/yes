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
