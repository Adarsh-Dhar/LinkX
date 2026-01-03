// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./MockERC20.sol";

/**
 * MockRouter - Simulates DEX swaps with hardcoded pricing
 * For testnet only - executes actual token transfers with fixed exchange rates
 * 
 * Hardcoded Rate: 1 USDC = 55 VVS
 */
contract MockRouter {
    
    // Hardcoded exchange rate: 1 USDC = 55 VVS
    uint256 public constant USDC_TO_VVS_RATE = 55;
    uint256 public constant VVS_TO_USDC_RATE = 1; // 55 VVS = 1 USDC
    
    // Token addresses (will be set to testnet addresses)
    address public USDC;
    address public VVS;
    address public WCRO;
    
    event SwapExecuted(
        address indexed sender,
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 amountOut
    );
    
    constructor(address _usdc, address _vvs, address _wcro) {
        USDC = _usdc;
        VVS = _vvs;
        WCRO = _wcro;
    }
    
    /**
     * Mock getAmountsOut - Returns hardcoded exchange amounts
     * @param amountIn Input amount (in token's decimals)
     * @param path Array of token addresses [tokenIn, tokenOut]
     * @return amounts Array of amounts [amountIn, amountOut]
     */
    function getAmountsOut(uint256 amountIn, address[] memory path) 
        external 
        view 
        returns (uint256[] memory amounts) 
    {
        require(path.length == 2, "MockRouter: INVALID_PATH");
        
        amounts = new uint256[](2);
        amounts[0] = amountIn;
        
        address tokenIn = path[0];
        address tokenOut = path[1];
        
        // USDC (6 decimals) -> VVS (18 decimals)
        if (tokenIn == USDC && tokenOut == VVS) {
            // 1 USDC (1000000) = 55 VVS (55000000000000000000)
            amounts[1] = amountIn * USDC_TO_VVS_RATE * 1e18 / 1e6;
        }
        // VVS (18 decimals) -> USDC (6 decimals)
        else if (tokenIn == VVS && tokenOut == USDC) {
            // 55 VVS (55000000000000000000) = 1 USDC (1000000)
            amounts[1] = amountIn * VVS_TO_USDC_RATE * 1e6 / (USDC_TO_VVS_RATE * 1e18);
        }
        // USDC -> WCRO (assume 1 USDC = 10 CRO)
        else if (tokenIn == USDC && tokenOut == WCRO) {
            amounts[1] = amountIn * 10 * 1e18 / 1e6;
        }
        // WCRO -> USDC (assume 10 CRO = 1 USDC)
        else if (tokenIn == WCRO && tokenOut == USDC) {
            amounts[1] = amountIn * 1e6 / (10 * 1e18);
        }
        // VVS -> WCRO (via USDC rate)
        else if (tokenIn == VVS && tokenOut == WCRO) {
            // VVS -> USDC -> WCRO
            uint256 usdcAmount = amountIn * VVS_TO_USDC_RATE * 1e6 / (USDC_TO_VVS_RATE * 1e18);
            amounts[1] = usdcAmount * 10 * 1e18 / 1e6;
        }
        // WCRO -> VVS (via USDC rate)
        else if (tokenIn == WCRO && tokenOut == VVS) {
            // WCRO -> USDC -> VVS
            uint256 usdcAmount = amountIn * 1e6 / (10 * 1e18);
            amounts[1] = usdcAmount * USDC_TO_VVS_RATE * 1e18 / 1e6;
        }
        else {
            revert("MockRouter: UNSUPPORTED_PAIR");
        }
        
        return amounts;
    }
    
    /**
     * Mock swapExactTokensForTokens - Executes swap with hardcoded rates
     * Performs actual token transfers using the mock ERC20 contracts
     */
    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts) {
        require(deadline >= block.timestamp, "MockRouter: EXPIRED");
        require(path.length == 2, "MockRouter: INVALID_PATH");
        require(amountIn > 0, "MockRouter: INVALID_AMOUNT");
        
        // Calculate output using hardcoded rates
        amounts = this.getAmountsOut(amountIn, path);
        
        require(amounts[1] >= amountOutMin, "MockRouter: INSUFFICIENT_OUTPUT_AMOUNT");
        
        address tokenIn = path[0];
        address tokenOut = path[1];
        
        // Transfer input token FROM sender TO this contract
        MockERC20 inToken = MockERC20(tokenIn);
        bool transferInSuccess = inToken.transferFrom(msg.sender, address(this), amountIn);
        require(transferInSuccess, "MockRouter: TRANSFER_IN_FAILED");
        
        // Mint output token directly to recipient (mock liquidity)
        MockERC20 outToken = MockERC20(tokenOut);
        outToken.mint(to, amounts[1]);
        
        emit SwapExecuted(msg.sender, tokenIn, tokenOut, amountIn, amounts[1]);
        
        return amounts;
    }
    
    /**
     * Get current hardcoded exchange rate
     */
    function getExchangeRate() external pure returns (uint256 usdcToVvs, uint256 vvsToUsdc) {
        return (USDC_TO_VVS_RATE, VVS_TO_USDC_RATE);
    }
}

