#!/bin/bash

# 🎯 QUICK START: Running Multiple Providers

echo "
╔════════════════════════════════════════════════════════════╗
║  🚀 Config-Driven Multi-Provider Alpha Server             ║
║  Start multiple hedge fund nodes with different configs   ║
╚════════════════════════════════════════════════════════════╝
"

echo "📋 Step 1: Verify providers.json exists"
if [ -f "providers.json" ]; then
    echo "✅ providers.json found"
    echo ""
    echo "Available Providers:"
    grep '"name"' providers.json | sed 's/.*"name": "/  - /' | sed 's/",//'
    echo ""
else
    echo "❌ providers.json not found!"
    exit 1
fi

echo "📋 Step 2: Install dependencies (if needed)"
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    exit 1
fi
echo "✅ Node.js is available"
echo ""

echo "📋 Step 3: Start servers"
echo ""
echo "To run all providers simultaneously, open these commands in separate terminals:"
echo ""
echo "Terminal 1 - Standard Node (Port 3050):"
echo "  cd server && node index.js"
echo ""
echo "Terminal 2 - Premium Node (Port 3051):"
echo "  cd server && PROVIDER_ID=premium node index.js"
echo ""
echo "Terminal 3 - Degen Node (Port 3052):"
echo "  cd server && PROVIDER_ID=scam node index.js"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Or use the helper script (if you have bash):"
echo ""
echo "  ./start_provider.sh"
echo "  ./start_provider.sh premium"
echo "  ./start_provider.sh scam"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📡 Testing the endpoints:"
echo ""
echo "# Get live price"
echo "  curl http://localhost:3050/market/price/CRO"
echo ""
echo "# Get alpha insight (will return 402 Payment Required)"
echo "  curl http://localhost:3050/alpha/insight/CRO"
echo ""
echo "# Check health"
echo "  curl http://localhost:3050/health"
echo ""
echo "✨ For more details, see CONFIG_DRIVEN_README.md"
echo ""
