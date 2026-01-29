// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "forge-std/Script.sol";
import "forge-std/console.sol";

import "../src/VVSFactory.sol";
import "../src/VVSRouter.sol";
import "../src/WXTZ.sol";
import "../src/USDC.sol";
// USDC is bridged, use interface only

contract DeployScript is Script {

    // Read from environment variables or deploy if not set
    address WXTZ_ADDR;
    address USDC_ADDR;

    function run() external {

        // Load addresses from .env, or deploy if not set
        string memory wxtzEnv = vm.envOr("WXTZ_ADDRESS", "");
        string memory usdcEnv = vm.envOr("USDC_CONTRACT", "");

        vm.startBroadcast();
        address deployer = msg.sender;

        // Deploy WXTZ if not set
        if (bytes(wxtzEnv).length == 0) {
            WXTZ wxtzDeployed = new WXTZ();
            WXTZ_ADDR = address(wxtzDeployed);
            console.log("WXTZ deployed at:", WXTZ_ADDR);
        } else {
            WXTZ_ADDR = vm.envAddress("WXTZ_ADDRESS");
            console.log("WXTZ (wrapped XTZ) at:", WXTZ_ADDR);
        }

        // Deploy USDC if not set
        if (bytes(usdcEnv).length == 0) {
            CronosCRC20 usdcDeployed = new CronosCRC20("USD Coin", "USDC", 6);
            USDC_ADDR = address(usdcDeployed);
            console.log("USDC deployed at:", USDC_ADDR);
        } else {
            USDC_ADDR = vm.envAddress("USDC_CONTRACT");
            console.log("USDC (bridged) at:", USDC_ADDR);
        }

        // 1. Deploy Factory
        VVSFactory factory = new VVSFactory(deployer);
        console.log("VVSFactory deployed at:", address(factory));
        // Print INIT_CODE_PAIR_HASH for VVSLibrary
        console.logBytes32(factory.INIT_CODE_PAIR_HASH());

        // 2. Use WXTZ and USDC
        WXTZ wxtz = WXTZ(payable(WXTZ_ADDR));

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