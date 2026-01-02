#!/usr/bin/env python3
"""
Test script for x402 payment flow
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the tool
from tools import access_paid_api

def main():
    print("="*60)
    print("Testing x402 Payment Flow")
    print("="*60)
    print()
    
    url = "http://localhost:3050/alpha/insight/CRO"
    print(f"Target URL: {url}")
    print()
    
    result = access_paid_api(url)
    
    print()
    print("="*60)
    print("FINAL RESULT:")
    print("="*60)
    print(result)
    print()
    
    # Check if successful
    if isinstance(result, dict) and result.get('success'):
        print("✅ Payment flow completed successfully!")
        return 0
    else:
        print("❌ Payment flow failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
