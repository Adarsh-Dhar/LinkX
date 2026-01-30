// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "forge-std/Script.sol";
import "forge-std/console.sol";
import "../src/WXTZ.sol";


contract DeployWXTZ is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("WALLET_PRIVATE_KEY");
        address bridge = vm.envAddress("BRIDGE_ADDRESS");
        vm.startBroadcast(deployerPrivateKey);
        new WXTZ(bridge);
        vm.stopBroadcast();
    }
}
