// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import {Script} from "forge-std/Script.sol";
import {TestWXTZ} from "../src/TestWXTZ.sol";
import {console} from "forge-std/console.sol";

contract DeployTestWXTZ is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("WALLET_PRIVATE_KEY");
        
        vm.startBroadcast(deployerPrivateKey);
        
        TestWXTZ token = new TestWXTZ();
        
        console.log("TestWXTZ deployed at:", address(token));
        console.log("Initial supply minted to:", msg.sender);
        console.log("You can mint more by calling: token.mint(address, amount)");
        
        vm.stopBroadcast();
    }
}
