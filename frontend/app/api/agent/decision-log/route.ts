import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

export async function GET() {
  // Get the 50 most recent TradeDecision entries, joined with trade and dataLog
  const logs = await prisma.tradeDecision.findMany({
    orderBy: { decidedAt: 'desc' },
    take: 50,
    include: {
      trade: true,
      dataLog: true
    }
  });
  return NextResponse.json({
    decisionLog: logs.map(l => ({
      decidedAt: l.decidedAt,
      action: l.trade?.strategy || 'N/A',
      token: l.trade?.tokenOut || 'N/A',
      signal: l.dataLog?.normalized ?? l.dataLog?.data,
      reason: l.trade?.reasoning || ''
    }))
  });
}
