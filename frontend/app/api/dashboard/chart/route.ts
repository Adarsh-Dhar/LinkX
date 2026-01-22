import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  try {
    // Fetch last 30 snapshots for the chart
    const snapshots = await prisma.portfolioSnapshot.findMany({
      orderBy: { timestamp: "asc" },
      take: 50, // Limit data points
      select: {
        timestamp: true,
        totalValueUsd: true,
      },
    });

    // Format for Recharts (or your charting lib)
    const chartData = snapshots.map((snap: { timestamp: string | number | Date; totalValueUsd: any; }) => ({
      time: new Date(snap.timestamp).toLocaleDateString(), // or .toLocaleTimeString()
      value: snap.totalValueUsd,
    }));

    return NextResponse.json(chartData);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch chart data" }, { status: 500 });
  }
}