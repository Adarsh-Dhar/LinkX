// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "forge-std/console.sol";

// Interfaces for the contracts (since they're in older Solidity versions)
interface IWXTZ {
    function name() external view returns (string memory);
    function symbol() external view returns (string memory);
    function decimals() external view returns (uint8);
    function totalSupply() external view returns (uint256);
    function balanceOf(address) external view returns (uint256);
    function allowance(address, address) external view returns (uint256);
    function deposit() external payable;
    function withdraw(uint256 wad) external;
    function transfer(address dst, uint256 wad) external returns (bool);
    function approve(address guy, uint256 wad) external returns (bool);
    function transferFrom(address src, address dst, uint256 wad) external returns (bool);
}

interface IUSDC {
    function name() external view returns (string memory);
    function symbol() external view returns (string memory);
    function decimals() external view returns (uint8);
    function totalSupply() external view returns (uint256);
    function balanceOf(address) external view returns (uint256);
    function native_denom() external view returns (string memory);
    function mint(address guy, uint256 wad) external;
    function burn(address guy, uint256 wad) external;
    function transfer(address dst, uint256 wad) external returns (bool);
    function approve(address guy, uint256 wad) external returns (bool);
    function transferFrom(address src, address dst, uint256 wad) external returns (bool);
    function setName(string memory name_) external;
}

interface IVVSFactory {
    function getPair(address tokenA, address tokenB) external view returns (address);
    function createPair(address tokenA, address tokenB) external returns (address);
    function allPairsLength() external view returns (uint256);
}

interface IEtherlinkVVSRouter {
    function factory() external view returns (address);
    function WXTZ() external view returns (address);
    function addLiquidityXTZ(
        address token,
        uint amountTokenDesired,
        uint amountTokenMin,
        uint amountXTZMin,
        address to,
        uint deadline
    ) external payable returns (uint amountToken, uint amountXTZ, uint liquidity);
    function getAmountsOut(uint amountIn, address[] calldata path) external view returns (uint[] memory amounts);
}

contract ContractTest is Test {
    IWXTZ public wxtz;
    IUSDC public usdc;
    IVVSFactory public factory;
    IEtherlinkVVSRouter public router;
    
    address public deployer;
    address public addr1;
    address public addr2;

    function setUp() public {
        console.log("\n========================================");
        console.log("Setting up test environment...");
        console.log("========================================\n");

        deployer = address(this);
        addr1 = vm.addr(1);
        addr2 = vm.addr(2);

        // Give test addresses some ETH
        vm.deal(addr1, 100 ether);
        vm.deal(addr2, 100 ether);

        // Deploy WXTZ
        bytes memory wxtzCode = vm.getCode("WXTZ.sol:WXTZ");
        address wxtzAddr;
        assembly {
            wxtzAddr := create(0, add(wxtzCode, 0x20), mload(wxtzCode))
        }
        wxtz = IWXTZ(wxtzAddr);
        console.log("WXTZ deployed:", wxtzAddr);

        // Deploy USDC
        bytes memory usdcCode = vm.getCode("USDC.sol:CronosCRC20");
        bytes memory usdcArgs = abi.encode("USD Coin", "ibc/usdc", uint8(6));
        bytes memory usdcBytecode = abi.encodePacked(usdcCode, usdcArgs);
        address usdcAddr;
        assembly {
            usdcAddr := create(0, add(usdcBytecode, 0x20), mload(usdcBytecode))
        }
        usdc = IUSDC(usdcAddr);
        console.log("USDC deployed:", usdcAddr);

        // Deploy VVS Factory
        bytes memory factoryCode = vm.getCode("VVSFactory.sol:VVSFactory");
        bytes memory factoryArgs = abi.encode(deployer);
        bytes memory factoryBytecode = abi.encodePacked(factoryCode, factoryArgs);
        address factoryAddr;
        assembly {
            factoryAddr := create(0, add(factoryBytecode, 0x20), mload(factoryBytecode))
        }
        factory = IVVSFactory(factoryAddr);
        console.log("VVS Factory deployed:", factoryAddr);

        // Deploy Etherlink VVS Router
        bytes memory routerCode = vm.getCode("VVSRouter.sol:EtherlinkVVSRouter");
        bytes memory routerArgs = abi.encode(factoryAddr, wxtzAddr);
        bytes memory routerBytecode = abi.encodePacked(routerCode, routerArgs);
        address routerAddr;
        assembly {
            routerAddr := create(0, add(routerBytecode, 0x20), mload(routerBytecode))
        }
        router = IEtherlinkVVSRouter(routerAddr);
        console.log("Etherlink VVS Router deployed:", routerAddr);
        console.log("");
    }

    // ========================
    // WXTZ Tests
    // ========================
    
    function test_WXTZ_InitialProperties() public view {
        console.log("Testing WXTZ initial properties...");
        assertEq(wxtz.name(), "Wrapped XTZ");
        assertEq(wxtz.symbol(), "WXTZ");
        assertEq(wxtz.decimals(), 18);
        assertEq(wxtz.totalSupply(), 0);
        console.log("  PASS: Initial properties correct");
    }

    function test_WXTZ_Deposit() public {
        console.log("Testing WXTZ deposit...");
        uint256 depositAmount = 10 ether;
        
        vm.prank(addr1);
        wxtz.deposit{value: depositAmount}();
        
        assertEq(wxtz.balanceOf(addr1), depositAmount);
        assertEq(wxtz.totalSupply(), depositAmount);
        console.log("  PASS: Deposit successful");
    }

    function test_WXTZ_Withdraw() public {
        console.log("Testing WXTZ withdraw...");
        uint256 depositAmount = 10 ether;
        uint256 withdrawAmount = 5 ether;
        
        vm.prank(addr1);
        wxtz.deposit{value: depositAmount}();
        
        uint256 balanceBefore = addr1.balance;
        
        vm.prank(addr1);
        wxtz.withdraw(withdrawAmount);
        
        assertEq(wxtz.balanceOf(addr1), 5 ether);
        assertEq(addr1.balance, balanceBefore + withdrawAmount);
        console.log("  PASS: Withdrawal successful");
    }

    function test_WXTZ_Transfer() public {
        console.log("Testing WXTZ transfer...");
        uint256 depositAmount = 10 ether;
        uint256 transferAmount = 2 ether;
        
        vm.prank(addr1);
        wxtz.deposit{value: depositAmount}();
        
        vm.prank(addr1);
        wxtz.transfer(addr2, transferAmount);
        
        assertEq(wxtz.balanceOf(addr1), 8 ether);
        assertEq(wxtz.balanceOf(addr2), transferAmount);
        console.log("  PASS: Transfer successful");
    }

    function test_WXTZ_ApproveAndTransferFrom() public {
        console.log("Testing WXTZ approve and transferFrom...");
        uint256 depositAmount = 10 ether;
        uint256 approveAmount = 3 ether;
        
        vm.prank(addr1);
        wxtz.deposit{value: depositAmount}();
        
        vm.prank(addr1);
        wxtz.approve(addr2, approveAmount);
        
        assertEq(wxtz.allowance(addr1, addr2), approveAmount);
        
        vm.prank(addr2);
        wxtz.transferFrom(addr1, addr2, approveAmount);
        
        assertEq(wxtz.balanceOf(addr1), 7 ether);
        assertEq(wxtz.balanceOf(addr2), approveAmount);
        console.log("  PASS: Approve and transferFrom successful");
    }

    // ========================
    // USDC Tests
    // ========================
    
    function test_USDC_InitialProperties() public view {
        console.log("Testing USDC initial properties...");
        assertEq(usdc.name(), "USD Coin");
        assertEq(usdc.symbol(), "ibc/usdc");
        assertEq(usdc.decimals(), 6);
        assertEq(usdc.native_denom(), "ibc/usdc");
        assertEq(usdc.totalSupply(), 0);
        console.log("  PASS: Initial properties correct");
    }

    function test_USDC_Mint() public {
        console.log("Testing USDC mint...");
        uint256 mintAmount = 1000 * 10**6; // 1000 USDC
        
        usdc.mint(addr1, mintAmount);
        
        assertEq(usdc.balanceOf(addr1), mintAmount);
        assertEq(usdc.totalSupply(), mintAmount);
        console.log("  PASS: Mint successful");
    }

    function test_USDC_Transfer() public {
        console.log("Testing USDC transfer...");
        uint256 mintAmount = 1000 * 10**6;
        uint256 transferAmount = 100 * 10**6;
        
        usdc.mint(addr1, mintAmount);
        
        vm.prank(addr1);
        usdc.transfer(addr2, transferAmount);
        
        assertEq(usdc.balanceOf(addr1), 900 * 10**6);
        assertEq(usdc.balanceOf(addr2), transferAmount);
        console.log("  PASS: Transfer successful");
    }

    function test_USDC_ApproveAndTransferFrom() public {
        console.log("Testing USDC approve and transferFrom...");
        uint256 mintAmount = 1000 * 10**6;
        uint256 approveAmount = 50 * 10**6;
        
        usdc.mint(addr1, mintAmount);
        
        vm.prank(addr1);
        usdc.approve(addr2, approveAmount);
        
        vm.prank(addr2);
        usdc.transferFrom(addr1, addr2, approveAmount);
        
        assertEq(usdc.balanceOf(addr1), 950 * 10**6);
        assertEq(usdc.balanceOf(addr2), approveAmount);
        console.log("  PASS: Approve and transferFrom successful");
    }

    function test_USDC_Burn() public {
        console.log("Testing USDC burn...");
        uint256 mintAmount = 1000 * 10**6;
        uint256 burnAmount = 50 * 10**6;
        
        usdc.mint(addr1, mintAmount);
        
        uint256 supplyBefore = usdc.totalSupply();
        usdc.burn(addr1, burnAmount);
        
        assertEq(usdc.balanceOf(addr1), 950 * 10**6);
        assertEq(usdc.totalSupply(), supplyBefore - burnAmount);
        console.log("  PASS: Burn successful");
    }

    function test_USDC_SetName() public {
        console.log("Testing USDC setName...");
        usdc.setName("USDC Updated");
        assertEq(usdc.name(), "USDC Updated");
        
        // Revert back
        usdc.setName("USD Coin");
        console.log("  PASS: Name update successful");
    }

    function test_RevertWhen_NonOwnerMintsUSDC() public {
        console.log("Testing USDC non-owner mint (should revert)...");
        vm.prank(addr1);
        vm.expectRevert();
        usdc.mint(addr1, 100 * 10**6);
    }

    // ========================
    // VVS Router Tests
    // ========================
    
    function test_VVSRouter_Configuration() public view {
        console.log("Testing Etherlink VVS Router configuration...");
        assertEq(router.factory(), address(factory));
        assertEq(router.WXTZ(), address(wxtz));
        console.log("  PASS: Router configuration correct");
    }

    function test_VVSRouter_AddLiquidityXTZ() public {
        console.log("Testing Etherlink VVS Router add liquidity XTZ...");
        uint256 usdcAmount = 1000 * 10**6;
        uint256 xtzAmount = 1 ether;
        
        // Mint USDC
        usdc.mint(address(this), usdcAmount);
        
        // Approve router
        usdc.approve(address(router), usdcAmount);
        
        // Create pair
        factory.createPair(address(usdc), address(wxtz));
        
        // Add liquidity
        uint256 deadline = block.timestamp + 3600;
        router.addLiquidityXTZ{value: xtzAmount}(
            address(usdc),
            usdcAmount,
            0,
            0,
            address(this),
            deadline
        );
        
        address pair = factory.getPair(address(usdc), address(wxtz));
        assertTrue(pair != address(0));
        console.log("  PASS: Liquidity added successfully");
    }

    // ========================
    // Integration Tests
    // ========================
    
    function test_Integration_FullWorkflow() public {
        console.log("Testing full integration workflow...");
        
        // Verify all contracts connected
        assertEq(router.factory(), address(factory));
        assertEq(router.WXTZ(), address(wxtz));
        
        // Deposit WXTZ
        vm.prank(addr1);
        wxtz.deposit{value: 5 ether}();
        
        // Approve router
        vm.prank(addr1);
        wxtz.approve(address(router), 5 ether);
        
        assertEq(wxtz.allowance(addr1, address(router)), 5 ether);
        console.log("  PASS: Integration workflow successful");
    }

    function test_DisplayDeploymentAddresses() public view {
        console.log("\n============================================================");
        console.log("DEPLOYMENT ADDRESSES");
        console.log("============================================================");
        console.log("WXTZ:        ", address(wxtz));
        console.log("USDC:        ", address(usdc));
        console.log("VVS Factory: ", address(factory));
        console.log("VVS Router:  ", address(router));
        console.log("============================================================\n");
    }

    // Fallback to receive XTZ
    receive() external payable {}
}
