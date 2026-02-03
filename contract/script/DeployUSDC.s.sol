// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "forge-std/Script.sol";
import "forge-std/console.sol";
import "../src/USDC.sol";

contract DeployUSDC is Script {
    function run() external {
        vm.startBroadcast();
        address deployer = msg.sender;
        USDC usdc = new USDC(deployer);
        console.log("USDC deployed at:", address(usdc));
        vm.stopBroadcast();
    }
}
