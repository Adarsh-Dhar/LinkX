// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "forge-std/Script.sol";
import "../src/WXTZ.sol";

contract DeployWXTZ is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("WALLET_PRIVATE_KEY");
        // Ensure this is the Etherlink precompile: 0xff00000000000000000000000000000000000001
        address bridge = vm.envAddress("BRIDGE_ADDRESS");
        
        vm.startBroadcast(deployerPrivateKey);

            // High-level deployment
            WXTZ wxtz = new WXTZ(bridge);
        
        console.log("WXTZ deployed at:", address(wxtz));

        vm.stopBroadcast();
    }
}