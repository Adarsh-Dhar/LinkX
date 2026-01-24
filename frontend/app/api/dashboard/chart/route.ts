import { NextResponse } from "next/server";

// SEARCH CONFIGURATION
// We switch to Ethereum Mainnet ('eth') to get the most liquid/active price feed
const NETWORK = "eth"; 
const QUERY = "ETH USDC"; 
const SEARCH_URL = `https://api.geckoterminal.com/api/v2/search/pools?query=${encodeURIComponent(QUERY)}&network=${NETWORK}`;

export async function GET() {
  try {
    // 1. Find the best ETH/USDC pool (usually Uniswap V3)
    const searchRes = await fetch(SEARCH_URL, {
      headers: { "Accept": "application/json" },
      next: { revalidate: 3600 } // Cache pool address for 1 hour
    });
    
    if (!searchRes.ok) throw new Error(`Pool Search Failed: ${searchRes.status}`);
    
    const searchData = await searchRes.json();
    const topPool = searchData.data?.[0];

    if (!topPool) throw new Error("No ETH/USDC pool found on GeckoTerminal");
    
    const poolAddress = topPool.attributes.address;

    // 2. Fetch Real-Time Candles (OHLCV)
    const ohlcvUrl = `https://api.geckoterminal.com/api/v2/networks/${NETWORK}/pools/${poolAddress}/ohlcv/minute?aggregate=1&limit=100`;
    
    const chartRes = await fetch(ohlcvUrl, {
      cache: "no-store", // CRITICAL: Real-time data
    });

    if (!chartRes.ok) throw new Error(`OHLCV Fetch Failed: ${chartRes.status}`);

    const chartJson = await chartRes.json();
    const candles = chartJson.data.attributes.ohlcv_list;

    // 3. Format
    const chartData = candles.map((c: any) => ({
      time: new Date(c[0] * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      value: c[4], // Close Price
      fullDate: c[0] * 1000
    })).reverse();

    return NextResponse.json(chartData);

  } catch (error: any) {
    console.error("❌ Chart API Error:", error.message);
    // Fallback if API fails (Static ETH price ~2500)
    const now = Date.now();
    return NextResponse.json(Array.from({ length: 20 }).map((_, i) => ({
      time: new Date(now - (20 - i) * 60000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      value: 2500 + Math.random() * 5,
      fullDate: now - (20 - i) * 60000
    })));
  }
}