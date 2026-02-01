import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Proxying the MarketAnalyst server
    const res = await fetch('http://localhost:3050/api/prices', { 
      cache: 'no-store',
      signal: AbortSignal.timeout(5000) // 5 second timeout
    });
    
    if (!res.ok) {
      throw new Error(`Server error: ${res.status}`);
    }
    
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    // Server not available, return mock data with 60 historical points
    const mockData = Array.from({ length: 60 }, (_, i) => {
      const minutesAgo = 59 - i;
      const timestamp = new Date(Date.now() - minutesAgo * 60000);
      const hour = String(timestamp.getHours()).padStart(2, '0');
      const minute = String(timestamp.getMinutes()).padStart(2, '0');
      const second = String(timestamp.getSeconds()).padStart(2, '0');
      const timeStr = `${hour}:${minute}:${second}`;
      
      // Create realistic price movement
      const basePrice = 0.06;
      const volatility = Math.sin(i * 0.1) * 0.003 + (Math.random() * 0.001 - 0.0005);
      const close = basePrice + volatility;
      
      return {
        time: timeStr,
        close: parseFloat(close.toFixed(6))
      };
    });
    
    return NextResponse.json(mockData);
  }
}