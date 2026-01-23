import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

export async function GET() {
  // Sum all data costs and trade profits
  const dataLogs = await prisma.dataLog.findMany();
  const tradeDecisions = await prisma.tradeDecision.findMany({ include: { trade: true } });

  const cost = dataLogs.reduce((sum, l) => sum + (typeof l.normalized === 'number' ? Math.abs(l.normalized) : 0), 0);
  const profit = tradeDecisions.reduce((sum, d) => sum + (d.trade?.realizedPnL || 0), 0);

  return NextResponse.json({
    roi: { cost, profit }
  });
}
