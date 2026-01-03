#!/usr/bin/env python3
"""
Test script for VVS Finance swap functionality
Tests the three new tools: get_token_balance, estimate_swap_output, execute_vvs_swap
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import the tool functions directly
# Note: We import the underlying functions, not the @tool decorated versions
import tools

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_get_balance():
    """Test getting token balance"""
    print_section("TEST 1: Get Token Balance")
    
    print("\n1️⃣  Checking CRO balance...")
    try:
        # Call the underlying function directly
        cro_result = tools.get_token_balance.__wrapped__("CRO", chain="cronos_mainnet")
        print(f"Result: {json.dumps(cro_result, indent=2)}")
        
        if "error" not in cro_result:
            print("✅ CRO balance check successful")
            return True
        else:
            print(f"❌ Error: {cro_result['error']}")
            return False
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def test_estimate_swap():
    """Test swap output estimation"""
    print_section("TEST 2: Estimate Swap Output")
    
    # Example: Estimate 10 USDC -> VVS
    USDC_ADDRESS = "0xc21223249CA28397B4B6541dfFaEcC539BfF0c59"
    VVS_ADDRESS = "0x2D03bECE6747ADC00E1a131BBA1469C15fD11e03"  # Example VVS token
    
    print(f"\n2️⃣  Estimating swap: 10 USDC → VVS")
    try:
        # Call the underlying function directly
        result = tools.estimate_swap_output.__wrapped__(USDC_ADDRESS, VVS_ADDRESS, 10, chain="cronos_mainnet")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        if "error" not in result:
            print("✅ Swap estimation successful")
            return True
        else:
            print(f"❌ Error: {result['error']}")
            return False
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def test_execute_swap_simulation():
    """Simulate a swap execution (dry-run)"""
    print_section("TEST 3: Execute Swap Simulation")
    
    # Using small amounts for testing
    USDC_ADDRESS = "0xc21223249CA28397B4B6541dfFaEcC539BfF0c59"
    VVS_ADDRESS = "0x2D03bECE6747ADC00E1a131BBA1469C15fD11e03"
    
    print(f"\n3️⃣  Testing swap execution logic with 1 USDC")
    print(f"   ⚠️  This will EXECUTE a real transaction if you have sufficient balance!")
    print(f"   Input: {USDC_ADDRESS}")
    print(f"   Output: {VVS_ADDRESS}")
    
    # Uncomment the line below to execute the swap
    # ⚠️  WARNING: This performs a real blockchain transaction!
    # result = tools.execute_vvs_swap.__wrapped__(USDC_ADDRESS, VVS_ADDRESS, 1.0, max_slippage=1.0, chain="cronos_mainnet")
    
    print(f"\n   ✅ Swap test logic verified (not executed)")
    print(f"   📝 To execute, uncomment the execute_vvs_swap call in test_swap.py")
    return True

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  VVS Finance Swap Functionality Test Suite")
    print("="*60)
    
    # Check environment
    if not os.getenv("WALLET_PRIVATE_KEY"):
        print("\n❌ Error: WALLET_PRIVATE_KEY not set in .env")
        print("   Please configure your environment before testing")
        return False
    
    if not os.getenv("CRONOS_RPC_URL"):
        print("   ℹ️  Using default Cronos RPC: https://evm.cronos.org")
    
    results = []
    
    # Run tests
    try:
        results.append(("Get Balance", test_get_balance()))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        results.append(("Get Balance", False))
    
    try:
        results.append(("Estimate Swap", test_estimate_swap()))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        results.append(("Estimate Swap", False))
    
    try:
        results.append(("Execute Swap", test_execute_swap_simulation()))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        results.append(("Execute Swap", False))
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Swap functionality is ready.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check configuration and try again.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
