#!/bin/bash

# Multi-Provider Server Launcher Script
# This script makes it easy to spawn multiple "Hedge Fund Nodes" with different configurations

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀  Multi-Provider Alpha Server Launcher${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}\n"

# Function to display usage
usage() {
    echo "Usage: $0 [provider_id]"
    echo ""
    echo "Available Providers:"
    echo "  default   - Standard Node (Port 3050, 0.1 USDC, Bullish)"
    echo "  premium   - Quant Elite (Port 3051, 1.0 USDC, Bullish)"
    echo "  scam      - Degen Calls (Port 3052, 0.01 USDC, Bearish)"
    echo ""
    echo "Examples:"
    echo "  $0                # Runs 'default' provider"
    echo "  $0 premium        # Runs 'premium' provider"
    echo "  $0 scam           # Runs 'scam' provider"
    echo ""
    echo "To run multiple providers simultaneously, open separate terminal windows:"
    echo "  Terminal 1: $0"
    echo "  Terminal 2: $0 premium"
    echo "  Terminal 3: $0 scam"
    exit 1
}

# Show help if requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
fi

# Get the provider ID (default to 'default')
PROVIDER_ID="${1:-default}"

echo -e "${YELLOW}Starting provider: ${PROVIDER_ID}${NC}\n"

# Export the PROVIDER_ID and start the server
export PROVIDER_ID=$PROVIDER_ID
node index.js
