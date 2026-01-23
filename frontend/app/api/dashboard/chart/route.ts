import { NextResponse } from "next/server";

// CoinGecko API for real price history (e.g., CRO/USDC)
const COINGECKO_API = "https://api.coingecko.com/api/v3/coins/cronos/market_chart?vs_currency=usd&days=30&interval=daily";

export async function GET() {
  try {
    const res = await fetch(COINGECKO_API);
    if (!res.ok) throw new Error("Failed to fetch from CoinGecko");
    const data = await res.json();
    // data.prices: [ [timestamp, price], ... ]
    const chartData = (data.prices || []).map(([ts, price]: [number, number]) => ({
      time: new Date(ts).toLocaleDateString(),
      value: price,
    }));
    return NextResponse.json(chartData);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch chart data" }, { status: 500 });
  }
}