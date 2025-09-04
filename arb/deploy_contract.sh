#!/bin/bash

echo "📝 Deploying Flash Loan Arbitrage Contract..."

# Create Solidity contract
cat > rust-engine/contracts/FlashLoanArbitrage.sol << 'EOF'
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IFlashLoanReceiver {
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool);
}

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

interface IPair {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
}

interface IPool {
    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

contract FlashLoanArbitrage is IFlashLoanReceiver {
    address private owner;
    IPool private constant AAVE_POOL = IPool(0x794a61358D6845594F94dc1DB02A252b5b4814aD);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    function executeArbitrage(
        address tokenBorrow,
        uint256 amount,
        address buyPair,
        address sellPair
    ) external onlyOwner {
        bytes memory params = abi.encode(buyPair, sellPair);
        AAVE_POOL.flashLoanSimple(address(this), tokenBorrow, amount, params, 0);
    }
    
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == address(AAVE_POOL), "Invalid caller");
        require(initiator == address(this), "Invalid initiator");
        
        (address buyPair, address sellPair) = abi.decode(params, (address, address));
        
        // Execute arbitrage
        IERC20(asset).approve(buyPair, amount);
        
        // Buy on first DEX
        IPair(buyPair).swap(amount, 0, address(this), "");
        
        // Sell on second DEX  
        uint256 tokenBalance = IERC20(asset).balanceOf(address(this));
        IERC20(asset).approve(sellPair, tokenBalance);
        IPair(sellPair).swap(0, tokenBalance, address(this), "");
        
        // Repay flash loan
        uint256 amountOwed = amount + premium;
        IERC20(asset).approve(address(AAVE_POOL), amountOwed);
        
        return true;
    }
    
    function withdraw(address token) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).transfer(owner, balance);
    }
    
    receive() external payable {}
}
EOF

echo "Contract created at: rust-engine/contracts/FlashLoanArbitrage.sol"
echo ""
echo "To deploy:"
echo "1. Use Remix IDE: https://remix.ethereum.org"
echo "2. Copy the contract code"
echo "3. Deploy to Arbitrum"
echo "4. Update executor_contract address in flash_loan.rs"