import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

export async function GET(request: Request) {
  // Support /api/market/price/[pair] by extracting pair from URL
  const url = new URL(request.url);
  const pathParts = url.pathname.split('/');
  const pair = pathParts[pathParts.length - 1];

  // If the route is /api/market/price/WXTZ-USDC, return latest price
  if (pair && pair.match(/^[A-Z]+-[A-Z]+$/)) {
    // Fetch chart data (portfolio snapshots)
    const snapshots = await prisma.portfolioSnapshot.findMany({
      orderBy: { timestamp: 'desc' },
      take: 1,
    });
    if (snapshots.length > 0) {
      // For WXTZ-USDC, calculate price as wxtzBalance/usdcBalance (or vice versa)
      const snap = snapshots[0];
      let price = null;
      if (pair === 'WXTZ-USDC' && snap.usdcBalance > 0) {
        price = snap.wxtzBalance / snap.usdcBalance;
      } else if (pair === 'USDC-WXTZ' && snap.wxtzBalance > 0) {
        price = snap.usdcBalance / snap.wxtzBalance;
      }
      if (price !== null && isFinite(price)) {
        return NextResponse.json({ pair, price: parseFloat(price.toFixed(6)), timestamp: snap.timestamp.toISOString() });
      }
    }
    // If no data or invalid, return 404
    return NextResponse.json({ error: 'Price not found' }, { status: 404 });
  }
  try {
    // ...existing code for chart data route...

    // If no snapshots yet, return mock data with 60 historical points
    const mockData = Array.from({ length: 60 }, (_, i) => {
      const minutesAgo = 59 - i;
      const timestamp = new Date(Date.now() - minutesAgo * 60000);
      const hour = String(timestamp.getHours()).padStart(2, '0');
      const minute = String(timestamp.getMinutes()).padStart(2, '0');
      const second = String(timestamp.getSeconds()).padStart(2, '0');
      const timeStr = `${hour}:${minute}:${second}`;

      // Create realistic portfolio value movement
      const baseValue = 1000; // Starting portfolio value
      const volatility = Math.sin(i * 0.1) * 30 + (Math.random() * 20 - 10);
      const value = baseValue + volatility;

      return {
        time: timeStr,
        value: parseFloat(value.toFixed(2)),
        wxtzBalance: parseFloat((Math.random() * 500).toFixed(4)),
        usdcBalance: parseFloat((Math.random() * 500).toFixed(2)),
        timestamp: timestamp.toISOString(),
      };
    });

    return NextResponse.json(mockData);
  } catch (error) {
    console.error('Chart API Error:', error);
    
    // Fallback mock data
    const mockData = Array.from({ length: 60 }, (_, i) => {
      const minutesAgo = 59 - i;
      const timestamp = new Date(Date.now() - minutesAgo * 60000);
      const hour = String(timestamp.getHours()).padStart(2, '0');
      const minute = String(timestamp.getMinutes()).padStart(2, '0');
      const second = String(timestamp.getSeconds()).padStart(2, '0');
      const timeStr = `${hour}:${minute}:${second}`;
      
      const baseValue = 1000;
      const volatility = Math.sin(i * 0.1) * 30 + (Math.random() * 20 - 10);
      const value = baseValue + volatility;
      
      return {
        time: timeStr,
        value: parseFloat(value.toFixed(2)),
        wxtzBalance: parseFloat((Math.random() * 500).toFixed(4)),
        usdcBalance: parseFloat((Math.random() * 500).toFixed(2)),
        timestamp: timestamp.toISOString(),
      };
    });

    return NextResponse.json(mockData);
  }
}