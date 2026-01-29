// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "forge-std/Script.sol";
import "forge-std/console.sol";

import "../src/VVSFactory.sol";
import "../src/VVSRouter.sol";
import "../src/WXTZ.sol";
// USDC is bridged, use interface only

contract DeployScript is Script {
    address constant WXTZ_ADDR = 0xB1e000000000000000000000000000000051D8B1;
    address constant USDC_ADDR = 0x4C2000000000000000000000000000000048494C;

    function run() external {
        // Start recording transactions to be sent
        vm.startBroadcast();

        address deployer = msg.sender;

        // 1. Deploy Factory
        VVSFactory factory = new VVSFactory(deployer);
        console.log("VVSFactory deployed at:", address(factory));
        // Print INIT_CODE_PAIR_HASH for VVSLibrary
        console.logBytes32(factory.INIT_CODE_PAIR_HASH());

        // 2. Deploy Tokens
        // Use deployed WXTZ and bridged USDC addresses on Etherlink Ghostnet
        WXTZ wxtz = WXTZ(payable(WXTZ_ADDR));
        console.log("WXTZ (wrapped XTZ) at:", address(wxtz));
        console.log("USDC (bridged) at:", USDC_ADDR);

        // 3. Deploy Router
            EtherlinkVVSRouter router = new EtherlinkVVSRouter(address(factory), WXTZ_ADDR);
        console.log("VVSRouter deployed at:", address(router));

        // ====================================================
        // 4. ADD LIQUIDITY
        // ====================================================

        // Approve Router for liquidity amounts (assumes deployer has WXTZ and USDC)
        wxtz.approve(address(router), 9 * 10**18);
        IERC20(USDC_ADDR).approve(address(router), 9000 * 10**6);

        // Add Liquidity (using 9 WXTZ and 9000 USDC)
        router.addLiquidity(
            WXTZ_ADDR,
            USDC_ADDR,
            9 * 10**18,
            9000 * 10**6,
            0,
            0,
            deployer, // Recipient of LP tokens
            block.timestamp + 300
        );

        console.log("Liquidity Added! Pair Created.");

        // Send remaining tokens to specified address (update this address for Etherlink if needed)
        address recipient = 0xb8552ec41cd7b5697464602d24d9c174F6FB863C; // Update if deploying to a different Etherlink address
        wxtz.transfer(recipient, 1 * 10**18);
        IERC20(USDC_ADDR).transfer(recipient, 1000 * 10**6);

        vm.stopBroadcast();
    }
}