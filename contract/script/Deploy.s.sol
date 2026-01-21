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
        // Start recording transactions to be sent
        vm.startBroadcast(); // <--- ADD THIS

        address deployer = msg.sender;

        // 1. Deploy Factory
        VVSFactory factory = new VVSFactory(deployer);
        console.log("VVSFactory deployed at:", address(factory));
            // Print INIT_CODE_PAIR_HASH for VVSLibrary
            console.logBytes32(factory.INIT_CODE_PAIR_HASH());

        // 2. Deploy Tokens
        WCRO wcro = new WCRO();
        console.log("WCRO deployed at:", address(wcro));

        CronosCRC20 usdc = new CronosCRC20("USD Coin", "USDC", 6);
        console.log("USDC deployed at:", address(usdc));

        // 3. Deploy Router
        VVSRouter router = new VVSRouter(address(factory), address(wcro));
        console.log("VVSRouter deployed at:", address(router));

        // ====================================================
        // 4. ADD LIQUIDITY
        // ====================================================

        uint256 amountWCRO = 1 * 10**18;
        uint256 amountUSDC = 1000 * 10**6;

        // Mint WCRO (Deposit CRO)
        wcro.deposit{value: amountWCRO}();

        // Mint USDC
        try usdc.mint(deployer, amountUSDC) { // Note: Changed address(this) to deployer usually, but kept logic similar
        } catch {}

        // Approve Router
        wcro.approve(address(router), amountWCRO);
        usdc.approve(address(router), amountUSDC);

        // Add Liquidity
        router.addLiquidity(
            address(wcro),
            address(usdc),
            amountWCRO,
            amountUSDC,
            0,
            0,
            deployer, // Recipient of LP tokens
            block.timestamp + 300
        );

        console.log("Liquidity Added! Pair Created.");

        vm.stopBroadcast(); // <--- ADD THIS
    }
}