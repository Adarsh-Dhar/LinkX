// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./MockERC20.sol";
import "./MockRouter.sol";

/**
 * Deploy Script for Mock DEX on Cronos Testnet
 * Deploys: USDC, VVS, WCRO tokens + MockRouter with 1 USDC = 55 VVS rate
 */
contract DeployMockDEX {
    
    MockERC20 public usdc;
    MockERC20 public vvs;
    MockERC20 public wcro;
    MockRouter public router;
    
    event Deployed(
        address usdc,
        address vvs,
        address wcro,
        address router
    );
    
    constructor() {
        // Deploy mock tokens
        usdc = new MockERC20("USD Coin", "USDC", 6);
        vvs = new MockERC20("VVS Finance", "VVS", 18);
        wcro = new MockERC20("Wrapped CRO", "WCRO", 18);
        
        // Deploy mock router with hardcoded rate
        router = new MockRouter(
            address(usdc),
            address(vvs),
            address(wcro)
        );
        
        // Mint initial supply for testing (router needs balances too)
        usdc.mint(msg.sender, 1000000 * 1e6);      // 1M USDC to deployer
        vvs.mint(msg.sender, 55000000 * 1e18);     // 55M VVS to deployer
        wcro.mint(msg.sender, 10000 * 1e18);       // 10K WCRO to deployer

        // Seed router with some tokens to cover transfer-based flows
        usdc.mint(address(router), 100000 * 1e6);  // 100k USDC
        vvs.mint(address(router), 5500000 * 1e18); // 5.5M VVS
        wcro.mint(address(router), 1000 * 1e18);   // 1k WCRO
        
        emit Deployed(
            address(usdc),
            address(vvs),
            address(wcro),
            address(router)
        );
    }
    
    function getAddresses() external view returns (
        address _usdc,
        address _vvs,
        address _wcro,
        address _router
    ) {
        return (
            address(usdc),
            address(vvs),
            address(wcro),
            address(router)
        );
    }
}
