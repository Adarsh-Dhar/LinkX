// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "forge-std/Script.sol";
import "forge-std/console.sol";
import "../src/WXTZ.sol";

contract DeployWXTZ is Script {
    function run() external {
        vm.startBroadcast();
        address deployer = msg.sender;
        WXTZ wxtz = new WXTZ(deployer);
        console.log("WXTZ deployed at:", address(wxtz));
        vm.stopBroadcast();
    }
}
