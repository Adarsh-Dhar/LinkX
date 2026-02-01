import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

export async function GET() {
  try {
    // Fetch portfolio snapshots from database with historical data
    // Get up to 60 recent snapshots (1 per minute = 1 hour of data)
    const snapshots = await prisma.portfolioSnapshot.findMany({
      orderBy: { timestamp: 'desc' },
      take: 60,
    });

    if (snapshots.length > 0) {
      // Reverse to get chronological order for chart
      const chartData = snapshots.reverse().map((snap) => {
        const hour = String(snap.timestamp.getHours()).padStart(2, '0');
        const minute = String(snap.timestamp.getMinutes()).padStart(2, '0');
        const second = String(snap.timestamp.getSeconds()).padStart(2, '0');
        const timeStr = `${hour}:${minute}:${second}`;

        return {
          time: timeStr,
          value: parseFloat(snap.totalValueUsd.toFixed(2)),
          wxtzBalance: parseFloat(snap.wxtzBalance.toFixed(4)),
          usdcBalance: parseFloat(snap.usdcBalance.toFixed(2)),
          timestamp: snap.timestamp.toISOString(),
        };
      });

      return NextResponse.json(chartData);
    }

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