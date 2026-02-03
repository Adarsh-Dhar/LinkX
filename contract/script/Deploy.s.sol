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

        // Load addresses from .env, or deploy if not set (try/catch for compatibility)

        vm.startBroadcast();
        address deployer = msg.sender;
        // Log deployer balance before any actions
        uint256 balance = deployer.balance;
        console.log("Deployer ETH/XTZ balance:", balance);

        // Try to get WXTZ address from env
        try vm.envAddress("WXTZ_ADDRESS") returns (address wxtzEnv) {
            WXTZ_ADDR = wxtzEnv;
            console.log("WXTZ (wrapped XTZ) at:", WXTZ_ADDR);
        } catch {
            WXTZ wxtzDeployed = new WXTZ(deployer);
            WXTZ_ADDR = address(wxtzDeployed);
            console.log("WXTZ deployed at:", WXTZ_ADDR);
        }

        // Try to get USDC address from env
        try vm.envAddress("USDC_CONTRACT") returns (address usdcEnv) {
            USDC_ADDR = usdcEnv;
            console.log("USDC (bridged) at:", USDC_ADDR);
        } catch {
            USDC usdcDeployed = new USDC(deployer);
            USDC_ADDR = address(usdcDeployed);
            console.log("USDC deployed at:", USDC_ADDR);
        }

        // 1. Deploy Factory
        VVSFactory factory = new VVSFactory(deployer);
        console.log("VVSFactory deployed at:", address(factory));
        // Print INIT_CODE_PAIR_HASH for VVSLibrary
        console.logBytes32(factory.INIT_CODE_PAIR_HASH());

        // 2. Use WXTZ and USDC
        WXTZ wxtz = WXTZ(payable(WXTZ_ADDR));
        USDC usdc = USDC(USDC_ADDR);

        // Ensure deployer has WXTZ and USDC for liquidity
        // 1. Mint 5 WXTZ to deployer
        wxtz.mint(deployer, 5 * 10**18);
        // 2. Mint 10,000 USDC to deployer
        usdc.mint(deployer, 10000 * 10**6);

        // 3. Deploy Router
        EtherlinkVVSRouter router = new EtherlinkVVSRouter(address(factory), WXTZ_ADDR);
        console.log("VVSRouter deployed at:", address(router));

        // ====================================================
        // 4. ADD LIQUIDITY
        // ====================================================

        // Approve Router for liquidity amounts (fit deployer's balance)
        wxtz.approve(address(router), 4 * 10**18);
        IERC20(USDC_ADDR).approve(address(router), 4000 * 10**6);

        // Add Liquidity (using 4 WXTZ and 4000 USDC)
        uint deadline = block.timestamp + 3600;
        router.addLiquidity(
            WXTZ_ADDR,
            USDC_ADDR,
            4 * 10**18,
            4000 * 10**6,
            0,
            0,
            deployer, // Recipient of LP tokens
            deadline
        );

        console.log("Liquidity Added! Pair Created.");

        // Send remaining tokens to specified address (update this address for Etherlink if needed)
        address recipient = 0xb8552ec41cd7b5697464602d24d9c174F6FB863C; // Update if deploying to a different Etherlink address
        wxtz.transfer(recipient, 1 * 10**18);
        IERC20(USDC_ADDR).transfer(recipient, 1000 * 10**6);

        vm.stopBroadcast();
    }
}