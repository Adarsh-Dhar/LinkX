// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "forge-std/Script.sol";
import "forge-std/console.sol";

import "../src/VVSFactory.sol";
import "../src/VVSRouter.sol";
import "../src/WXTZ.sol";
import "../src/USDC.sol";

contract DeployContractsScript is Script {
    function run() external {
        vm.startBroadcast();
        address deployer = msg.sender;
        // Deploy WXTZ
        WXTZ wxtz = new WXTZ();
        address wxtzAddr = address(wxtz);
        console.log("WXTZ deployed at:", wxtzAddr);
        // Deploy USDC
        CronosCRC20 usdc = new CronosCRC20("USD Coin", "USDC", 6);
        address usdcAddr = address(usdc);
        console.log("USDC deployed at:", usdcAddr);
        // Deploy Factory
        VVSFactory factory = new VVSFactory(deployer);
        address factoryAddr = address(factory);
        console.log("VVSFactory deployed at:", factoryAddr);
        // Deploy Router
        EtherlinkVVSRouter router = new EtherlinkVVSRouter(factoryAddr, wxtzAddr);
        address routerAddr = address(router);
        console.log("VVSRouter deployed at:", routerAddr);
        vm.stopBroadcast();
    }
}
