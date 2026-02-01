// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/// @title Test Wrapped XTZ - Mintable by owner for testing
contract TestWXTZ is ERC20, Ownable {
    constructor() ERC20("Test Wrapped XTZ", "TWXTZ") Ownable(msg.sender) {
        // Mint initial supply to deployer
        _mint(msg.sender, 10000 * 10**18); // 10,000 TWXTZ
    }

    /// @notice Mint tokens - only owner can call this
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    /// @notice Burn tokens from your own balance
    function burn(uint256 amount) external {
        _burn(msg.sender, amount);
    }
}
