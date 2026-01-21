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

        // Mint WCRO (Deposit CRO)
        wcro.deposit{value: 10 * 10**18}();

        // Mint USDC
        try usdc.mint(deployer, 10000 * 10**6) {
        } catch {}

        // Approve Router for liquidity amounts
        wcro.approve(address(router), 9 * 10**18);
        usdc.approve(address(router), 9000 * 10**6);

        // Add Liquidity (using 9 WCRO and 9000 USDC)
        router.addLiquidity(
            address(wcro),
            address(usdc),
            9 * 10**18,
            9000 * 10**6,
            0,
            0,
            deployer, // Recipient of LP tokens
            block.timestamp + 300
        );

        console.log("Liquidity Added! Pair Created.");

        // Send remaining tokens to specified address
        address recipient = 0xb8552ec41cd7b5697464602d24d9c174F6FB863C;
        wcro.transfer(recipient, 1 * 10**18);
        usdc.transfer(recipient, 1000 * 10**6);

        vm.stopBroadcast(); // <--- ADD THIS
    }
}