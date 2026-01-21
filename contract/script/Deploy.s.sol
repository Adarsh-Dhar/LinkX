// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "forge-std/Script.sol";
import "forge-std/console.sol";

import "../src/VVSFactory.sol";
import "../src/VVSRouter.sol";
import "../src/WCRO.sol";
import "../src/USDC.sol";

contract DeployScript is Script {
    function run() external {
        // Use msg.sender as deployer (set by forge script --private-key)
        address deployer = msg.sender;

        // 1. Deploy Factory
        VVSFactory factory = new VVSFactory(deployer);
        console.log("VVSFactory deployed at:", address(factory));

        // 2. Deploy Tokens
        WCRO wcro = new WCRO();
        console.log("WCRO deployed at:", address(wcro));

        CronosCRC20 usdc = new CronosCRC20("USD Coin", "USDC", 6);
        console.log("USDC deployed at:", address(usdc));

        // 3. Deploy Router
        VVSRouter router = new VVSRouter(address(factory), address(wcro));
        console.log("VVSRouter deployed at:", address(router));

        // ====================================================
        // 4. ADD LIQUIDITY (This "adds" them to VVS)
        // ====================================================

        // Define liquidity amounts (e.g., 1000 of each)
        uint256 amountWCRO = 1 * 10**18; // 1 CRO for demo, adjust as needed
        uint256 amountUSDC = 1000 * 10**6; // 1000 USDC

        // Mint WCRO to address(this) by calling deposit() and sending 1 CRO
        wcro.deposit{value: amountWCRO}();

        // Mint USDC to address(this) (if mint function exists)
        try usdc.mint(address(this), amountUSDC) {
            // Minted successfully
        } catch {
            // If mint not available, ignore
        }

        // A. APPROVE Router to spend tokens from address(this)
        wcro.approve(address(router), amountWCRO);
        usdc.approve(address(router), amountUSDC);
        console.log("Approved router to spend tokens");

        // B. Add Liquidity
        // This function creates the Pair contract automatically
        router.addLiquidity(
            address(wcro),
            address(usdc),
            amountWCRO,
            amountUSDC,
            0, // Min amount (0 for dev)
            0, // Min amount (0 for dev)
            address(this),
            block.timestamp + 300
        );
        console.log("Liquidity Added! Pair Created.");
    }
}