// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "forge-std/Script.sol";
import "forge-std/console.sol";
import "../src/VVSRouter.sol";

contract DeployVVSRouter is Script {
    function run() external {
        vm.startBroadcast();
        // Set these addresses before running or pass as env vars
        address factory = vm.envAddress("VVS_FACTORY_ADDRESS");
        address wxtz = vm.envAddress("WXTZ_ADDRESS");
        EtherlinkVVSRouter router = new EtherlinkVVSRouter(factory, wxtz);
        console.log("VVSRouter deployed at:", address(router));
        vm.stopBroadcast();
    }
}
