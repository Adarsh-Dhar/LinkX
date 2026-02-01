import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  try {
    // 1. Fetch Aggregates
    const tradeStats = await prisma.trade.aggregate({
      _count: {
        id: true,
        _all: true, // Total trades
      },
      _sum: {
        realizedPnL: true, // Total P&L
      },
      _avg: {
        confidence: true, // Avg Confidence
      },
    });

    // 2. Count Wins specifically
    const winCount = await prisma.trade.count({
      where: {
        isWin: true,
      },
    });

    // 3. Count Purchased Alpha Nodes
    const alphaCount = await prisma.alphaNode.count({
      where: {
        isPurchased: true,
      },
    });

    // 4. Calculate Win Rate
    const totalTrades = tradeStats._count._all;
    const winRate = totalTrades > 0 ? (winCount / totalTrades) * 100 : 0;

    // 5. Get Latest Portfolio Snapshot for "Wallet Balance"
    const latestSnapshot = await prisma.portfolioSnapshot.findFirst({
      orderBy: { timestamp: "desc" },
    });

    // 6. Calculate Percentage Growth (Simple Estimate)
    // (Total PnL / (Current Balance - Total PnL)) * 100
    // This assumes the balance grew purely from trading. 
    // For more accuracy, track "deposits" in DB.
    const currentBalanceUsd = latestSnapshot?.totalValueUsd || 0;
    const totalPnL = tradeStats._sum.realizedPnL || 0;
    const startingCapital = currentBalanceUsd - totalPnL;
    
    let profitPercent = 0;
    if (startingCapital > 0) {
      profitPercent = (totalPnL / startingCapital) * 100;
    }

    return NextResponse.json({
      wxtzBalance: latestSnapshot?.wxtzBalance || 0,
      usdcBalance: latestSnapshot?.usdcBalance || 0,
      walletBalanceUsd: currentBalanceUsd,
      alphaPurchased: alphaCount,
      totalPnL: totalPnL,
      profitPercent: profitPercent,
      winRate: winRate,
      totalTrades: totalTrades,
      avgConfidence: (tradeStats._avg.confidence || 0) * 100, // Convert 0.85 to 85.0
    });

  } catch (error) {
    console.error("Stats API Error:", error);
    return NextResponse.json({ error: "Failed to fetch stats" }, { status: 500 });
  }
}