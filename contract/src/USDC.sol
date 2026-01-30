// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "./ModuleCRC20.sol";

// Fully ERC20-compliant USDC contract for Etherlink
contract USDC is ModuleCRC20 {
    constructor() CronosCRC20("USD Coin", "USDC", 6) {}
}
