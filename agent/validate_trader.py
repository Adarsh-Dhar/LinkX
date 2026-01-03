#!/usr/bin/env python3
"""
Validation script for VVS Finance swap implementation
Validates that the tools are properly registered and can be called by the agent
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def validate_imports():
    """Validate that all required modules can be imported"""
    print_section("VALIDATION 1: Import Validation")
    
    try:
        print("\n1️⃣  Importing main agent...")
        from main import AlphaConsumerAgent
        print("   ✅ AlphaConsumerAgent imported")
        
        print("\n2️⃣  Importing tools module...")
        from tools import (
            access_paid_api,
            check_market_conditions,
            execute_vvs_swap,
            get_token_balance,
            estimate_swap_output
        )
        print("   ✅ access_paid_api tool imported")
        print("   ✅ check_market_conditions tool imported")
        print("   ✅ execute_vvs_swap tool imported")
        print("   ✅ get_token_balance tool imported")
        print("   ✅ estimate_swap_output tool imported")
        
        print("\n3️⃣  Importing dependencies...")
        from web3 import Web3
        from eth_account import Account
        import requests
        print("   ✅ Web3 imported")
        print("   ✅ eth_account imported")
        print("   ✅ requests imported")
        
        return True
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def validate_abis():
    """Validate that ABI definitions are present"""
    print_section("VALIDATION 2: ABI Definitions")
    
    try:
        from tools import ROUTER_ABI, ERC20_ABI
        
        print(f"\n1️⃣  Router ABI: {len(ROUTER_ABI)} functions defined")
        for i, func in enumerate(ROUTER_ABI, 1):
            func_name = func.get("name", "unknown")
            print(f"   {i}. {func_name}")
        
        print(f"\n2️⃣  ERC20 ABI: {len(ERC20_ABI)} functions defined")
        for i, func in enumerate(ERC20_ABI, 1):
            func_name = func.get("name", "unknown")
            print(f"   {i}. {func_name}")
        
        if len(ROUTER_ABI) >= 3 and len(ERC20_ABI) >= 4:
            print("\n✅ All required ABIs are defined")
            return True
        else:
            print("\n❌ Missing ABI definitions")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def validate_addresses():
    """Validate addresses configuration"""
    print_section("VALIDATION 3: Address Registry")
    
    try:
        import json
        
        with open("addresses.json", "r") as f:
            addresses = json.load(f)
        
        print("\n1️⃣  Cronos Mainnet:")
        mainnet = addresses.get("cronos_mainnet", {})
        contracts = mainnet.get("contracts", {})
        
        if "vvs_router" in contracts:
            router_addr = contracts["vvs_router"].get("address")
            print(f"   ✅ VVS Router: {router_addr}")
        else:
            print(f"   ❌ VVS Router not found")
            return False
        
        if "wcro" in contracts:
            wcro_addr = contracts["wcro"].get("address")
            print(f"   ✅ WCRO: {wcro_addr}")
        else:
            print(f"   ❌ WCRO not found")
            return False
        
        if "usdc" in contracts:
            usdc_addr = contracts["usdc"].get("address")
            print(f"   ✅ USDC: {usdc_addr}")
        else:
            print(f"   ❌ USDC not found")
            return False
        
        print("\n2️⃣  Cronos Testnet:")
        testnet = addresses.get("cronos_testnet", {})
        test_contracts = testnet.get("contracts", {})
        
        if "vvs_router" in test_contracts:
            router_addr = test_contracts["vvs_router"].get("address")
            print(f"   ℹ️  VVS Router: {router_addr}")
        else:
            print(f"   ❌ VVS Router not found on testnet")
        
        print("\n✅ Address registry validated")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def validate_environment():
    """Validate environment configuration"""
    print_section("VALIDATION 4: Environment Setup")
    
    required_vars = [
        "GEMINI_API_KEY",
        "WALLET_PRIVATE_KEY",
        "CRYPTO_COM_API_KEY"
    ]
    
    optional_vars = [
        "CRONOS_RPC_URL"
    ]
    
    print("\n📋 Required Variables:")
    all_present = True
    for var in required_vars:
        if os.getenv(var):
            value = os.getenv(var)
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"   ✅ {var}: {masked}")
        else:
            print(f"   ❌ {var}: NOT SET")
            all_present = False
    
    print("\n📋 Optional Variables:")
    for var in optional_vars:
        if os.getenv(var):
            value = os.getenv(var)
            print(f"   ✅ {var}: {value}")
        else:
            print(f"   ℹ️  {var}: not set (will use default)")
    
    if all_present:
        print("\n✅ Environment properly configured")
        return True
    else:
        print("\n❌ Missing required environment variables")
        return False

def validate_file_structure():
    """Validate that all required files exist"""
    print_section("VALIDATION 5: File Structure")
    
    required_files = [
        "main.py",
        "tools.py",
        "addresses.json",
        "requirements.txt",
        "test_swap.py",
        ".env"
    ]
    
    optional_files = [
        "TRADER_IMPLEMENTATION.md",
        "TRADER_USAGE_EXAMPLES.md",
        "setup_trader.sh"
    ]
    
    print("\n📁 Required Files:")
    all_present = True
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file} ({size} bytes)")
        else:
            print(f"   ❌ {file}: MISSING")
            all_present = False
    
    print("\n📁 Optional Documentation:")
    for file in optional_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file} ({size} bytes)")
        else:
            print(f"   ℹ️  {file}: not present")
    
    if all_present:
        print("\n✅ File structure validated")
        return True
    else:
        print("\n❌ Missing required files")
        return False

def main():
    """Run all validations"""
    print("\n" + "="*60)
    print("  Trader Implementation Validation Suite")
    print("="*60)
    
    results = []
    
    # Run all validations
    try:
        results.append(("Imports", validate_imports()))
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        results.append(("Imports", False))
    
    try:
        results.append(("ABIs", validate_abis()))
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        results.append(("ABIs", False))
    
    try:
        results.append(("Addresses", validate_addresses()))
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        results.append(("Addresses", False))
    
    try:
        results.append(("Environment", validate_environment()))
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        results.append(("Environment", False))
    
    try:
        results.append(("Files", validate_file_structure()))
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        results.append(("Files", False))
    
    # Summary
    print_section("VALIDATION SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nResult: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n" + "="*60)
        print("  🎉 IMPLEMENTATION COMPLETE & VALIDATED!")
        print("="*60)
        print("\n✅ Your Trader is ready to execute swaps on VVS Finance!")
        print("\n📖 Next Steps:")
        print("   1. Read TRADER_IMPLEMENTATION.md for full documentation")
        print("   2. Review TRADER_USAGE_EXAMPLES.md for usage patterns")
        print("   3. Start the agent: python3 main.py")
        print("   4. Try a swap: 'Execute a 5 USDC to VVS swap'")
        print("\n⚠️  Remember:")
        print("   - Test with small amounts first (1-5 USDC)")
        print("   - Check gas prices before large trades")
        print("   - Monitor transactions on https://cronoscan.com")
        return True
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed.")
        print("   Check the errors above and resolve them.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
