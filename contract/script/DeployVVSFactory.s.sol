// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "forge-std/Script.sol";
import "forge-std/console.sol";
import "../src/VVSFactory.sol";

contract DeployVVSFactory is Script {
    function run() external {
        vm.startBroadcast();
        address deployer = msg.sender;
        VVSFactory factory = new VVSFactory(deployer);
        console.log("VVSFactory deployed at:", address(factory));
        vm.stopBroadcast();
    }
}
