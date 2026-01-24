import { NextResponse } from "next/server";


// CoinGecko API for real price history (e.g., CRO/USDC)
const COINGECKO_API = "https://api.coingecko.com/api/v3/coins/crypto-com-chain/market_chart?vs_currency=usd&days=30&interval=daily";

// Simple in-memory cache (not for production use)
let cachedChartData: any = null;
let cacheTimestamp: number = 0;
const CACHE_TTL = 60 * 1000; // 1 minute

export async function GET() {
  try {
    // Use cache if recent
    if (cachedChartData && Date.now() - cacheTimestamp < CACHE_TTL) {
      return NextResponse.json(cachedChartData);
    }
    const res = await fetch(COINGECKO_API);
    if (!res.ok) throw new Error(`Failed to fetch from CoinGecko: ${res.status} ${res.statusText}`);
    const data = await res.json();
    // data.prices: [ [timestamp, price], ... ]
    const chartData = (data.prices || []).map(([ts, price]: [number, number]) => ({
      time: new Date(ts).toLocaleDateString(),
      value: price,
    }));
    // Update cache
    cachedChartData = chartData;
    cacheTimestamp = Date.now();
    return NextResponse.json(chartData);
  } catch (error: any) {
    // Log error for debugging
    console.error("[Chart API] Error:", error?.message || error);
    // Serve cached data if available
    if (cachedChartData) {
      return NextResponse.json(cachedChartData);
    }
    return NextResponse.json({ error: "Failed to fetch chart data" }, { status: 500 });
  }
}