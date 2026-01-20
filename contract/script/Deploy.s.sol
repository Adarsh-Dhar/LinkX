// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Script.sol";
import "forge-std/console.sol";

// Import interfaces for older Solidity versions
interface IWCRO {
    function name() external view returns (string memory);
    function symbol() external view returns (string memory);
    function decimals() external view returns (uint8);
}

interface IUSDC {
    function name() external view returns (string memory);
    function symbol() external view returns (string memory);
    function decimals() external view returns (uint8);
    function native_denom() external view returns (string memory);
}

interface IVVSRouter {
    function factory() external view returns (address);
    function WETH() external view returns (address);
}

contract DeployScript is Script {
            // Internal deploy helpers
            function _deployWCRO() internal returns (address) {
                console.log("Deploying WCRO...");
                bytes memory wcroCreationCode = vm.getCode("WCRO.sol:WCRO");
                address wcroAddress;
                assembly {
                    wcroAddress := create(0, add(wcroCreationCode, 0x20), mload(wcroCreationCode))
                }
                require(wcroAddress != address(0), "WCRO deployment failed");
                IWCRO wcro = IWCRO(wcroAddress);
                console.log("WCRO deployed to:", wcroAddress);
                console.log("  Name:", wcro.name());
                console.log("  Symbol:", wcro.symbol());
                console.log("  Decimals:", wcro.decimals());
                console.log("");
                return wcroAddress;
            }

            function _deployUSDC() internal returns (address) {
                console.log("Deploying USDC (CronosCRC20)...");
                bytes memory usdcCreationCode = vm.getCode("USDC.sol:CronosCRC20");
                bytes memory usdcConstructorArgs = abi.encode(
                    "USD Coin",      // name
                    "ibc/usdc",     // denom
                    uint8(6)        // decimals
                );
                bytes memory usdcBytecode = abi.encodePacked(usdcCreationCode, usdcConstructorArgs);
                address usdcAddress;
                assembly {
                    usdcAddress := create(0, add(usdcBytecode, 0x20), mload(usdcBytecode))
                }
                require(usdcAddress != address(0), "USDC deployment failed");
                IUSDC usdc = IUSDC(usdcAddress);
                console.log("USDC deployed to:", usdcAddress);
                console.log("  Name:", usdc.name());
                console.log("  Symbol:", usdc.symbol());
                console.log("  Decimals:", usdc.decimals());
                console.log("  Native Denom:", usdc.native_denom());
                console.log("");
                return usdcAddress;
            }

            function _deployFactory(address deployer) internal returns (address) {
                console.log("Deploying VVS Factory...");
                bytes memory factoryCreationCode = vm.getCode("VVSFactory.sol:VVSFactory");
                bytes memory factoryConstructorArgs = abi.encode(deployer);
                bytes memory factoryBytecode = abi.encodePacked(factoryCreationCode, factoryConstructorArgs);
                address factoryAddress;
                assembly {
                    factoryAddress := create(0, add(factoryBytecode, 0x20), mload(factoryBytecode))
                }
                require(factoryAddress != address(0), "Factory deployment failed");
                console.log("VVS Factory deployed to:", factoryAddress);
                console.log("");
                return factoryAddress;
            }

            function _deployRouter(address factoryAddress, address wcroAddress) internal returns (address) {
                console.log("Deploying VVS Router...");
                bytes memory routerCreationCode = vm.getCode("VVSRouter.sol:VVSRouter");
                bytes memory routerConstructorArgs = abi.encode(factoryAddress, wcroAddress);
                bytes memory routerBytecode = abi.encodePacked(routerCreationCode, routerConstructorArgs);
                address routerAddress;
                assembly {
                    routerAddress := create(0, add(routerBytecode, 0x20), mload(routerBytecode))
                }
                require(routerAddress != address(0), "Router deployment failed");
                IVVSRouter router = IVVSRouter(routerAddress);
                console.log("VVS Router deployed to:", routerAddress);
                console.log("  Factory:", router.factory());
                console.log("  WETH (WCRO):", router.WETH());
                console.log("");
                return routerAddress;
            }
        struct DeploySummary {
            address deployer;
            address wcroAddress;
            address usdcAddress;
            address factoryAddress;
            address routerAddress;
        }
    function run() external {
        console.log("\n========================================");
        console.log("Starting Deployment Process");
        console.log("========================================\n");

        // Get deployer info
        address deployer = tx.origin;
        console.log("Deploying contracts with account:", deployer);
        console.log("Account balance:", deployer.balance);
        console.log("");

        vm.startBroadcast();
        address wcroAddress = _deployWCRO();
        address usdcAddress = _deployUSDC();
        address factoryAddress = _deployFactory(deployer);
        address routerAddress = _deployRouter(factoryAddress, wcroAddress);
        vm.stopBroadcast();

        DeploySummary memory summary = DeploySummary({
            deployer: deployer,
            wcroAddress: wcroAddress,
            usdcAddress: usdcAddress,
            factoryAddress: factoryAddress,
            routerAddress: routerAddress
        });
        _logAndWriteSummary(summary);
    }

    function _logAndWriteSummary(DeploySummary memory summary) internal {
        // ========================
        // Summary
        // ========================
        console.log("============================================================");
        console.log("DEPLOYMENT SUMMARY");
        console.log("============================================================");
        console.log("WCRO Address:       ", summary.wcroAddress);
        console.log("USDC Address:       ", summary.usdcAddress);
        console.log("VVS Factory Address:", summary.factoryAddress);
        console.log("VVS Router Address: ", summary.routerAddress);
        console.log("============================================================");
        console.log("\nDeployment completed successfully!");
        console.log("");

        // Write addresses to file
        string memory json = string(abi.encodePacked(
            '{\n',
            '  "network": "', _getNetworkName(), '",\n',
            '  "deployer": "', vm.toString(summary.deployer), '",\n',
            '  "timestamp": "', vm.toString(block.timestamp), '",\n',
            '  "contracts": {\n',
            '    "WCRO": {\n',
            '      "address": "', vm.toString(summary.wcroAddress), '",\n',
            '      "name": "Wrapped CRO",\n',
            '      "symbol": "WCRO",\n',
            '      "decimals": "18"\n',
            '    },\n',
            '    "USDC": {\n',
            '      "address": "', vm.toString(summary.usdcAddress), '",\n',
            '      "name": "USD Coin",\n',
            '      "symbol": "ibc/usdc",\n',
            '      "decimals": "6",\n',
            '      "denom": "ibc/usdc"\n',
            '    },\n',
            '    "VVSFactory": {\n',
            '      "address": "', vm.toString(summary.factoryAddress), '"\n',
            '    },\n',
            '    "VVSRouter": {\n',
            '      "address": "', vm.toString(summary.routerAddress), '",\n',
            '      "factory": "', vm.toString(summary.factoryAddress), '",\n',
            '      "WETH": "', vm.toString(summary.wcroAddress), '"\n',
            '    }\n',
            '  }\n',
            '}'
        ));
        
        vm.writeFile("deployment-addresses.json", json);
        console.log("Deployment addresses saved to deployment-addresses.json");
        console.log("");
    }

    function _getNetworkName() internal view returns (string memory) {
        uint256 chainId = block.chainid;
        if (chainId == 1) return "mainnet";
        if (chainId == 5) return "goerli";
        if (chainId == 25) return "cronos_mainnet";
        if (chainId == 338) return "cronos_testnet";
        if (chainId == 31337) return "hardhat";
        return "unknown";
    }
}
