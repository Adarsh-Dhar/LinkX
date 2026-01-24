import { NextResponse } from "next/server";

// 1. CONFIGURATION: Ethereum Mainnet (High Liquidity/Volatility)
const NETWORK = "eth"; 
const QUERY = "ETH USDC"; 
const SEARCH_URL = `https://api.geckoterminal.com/api/v2/search/pools?query=${encodeURIComponent(QUERY)}&network=${NETWORK}`;

export async function GET() {
  try {
    // 2. Dynamic Pool Search
    const searchRes = await fetch(SEARCH_URL, {
      headers: { "Accept": "application/json" },
      next: { revalidate: 3600 } 
    });
    
    if (!searchRes.ok) throw new Error(`Pool Search Failed: ${searchRes.status}`);
    
    const searchData = await searchRes.json();
    const topPool = searchData.data?.[0];

    if (!topPool) throw new Error("No ETH/USDC pool found");
    
    const poolAddress = topPool.attributes.address;

    // 3. Fetch Real-Time Candles (OHLCV)
    const ohlcvUrl = `https://api.geckoterminal.com/api/v2/networks/${NETWORK}/pools/${poolAddress}/ohlcv/minute?aggregate=1&limit=100`;
    
    const chartRes = await fetch(ohlcvUrl, { cache: "no-store" });
    if (!chartRes.ok) throw new Error(`OHLCV Fetch Failed: ${chartRes.status}`);

    const chartJson = await chartRes.json();
    
    // 4. FORMAT FOR EXPERT TRADING
    // GeckoTerminal Format: [timestamp, open, high, low, close, volume]
    const expertData = chartJson.data.attributes.ohlcv_list.map((c: any) => ({
      time: new Date(c[0] * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      timestamp: c[0] * 1000,
      open: c[1],
      high: c[2],
      low: c[3],
      close: c[4],
      volume: c[5], // <--- CRITICAL: Volume included
    })).reverse(); // Oldest first for Pandas

    return NextResponse.json(expertData);

  } catch (error: any) {
    console.error("❌ Chart API Error:", error.message);
    // Fallback preventing crash
    return NextResponse.json([]);
  }
}