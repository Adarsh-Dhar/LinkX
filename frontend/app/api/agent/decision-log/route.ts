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
      reason: l.trade?.reasoning || '',
      context: l.context || ''
    }))
  });
}

export async function POST(request: Request) {
  // Accepts: tradeId, dataLogId, context, bias, confidence
  const body = await request.json();
  const { tradeId, dataLogId, context, bias, confidence } = body;
  if (!tradeId || !dataLogId) {
    return NextResponse.json({ error: 'tradeId and dataLogId required' }, { status: 400 });
  }
  const decision = await prisma.tradeDecision.create({
    data: {
      tradeId,
      dataLogId,
      context: context || null,
      execution_bias: bias || null,
      risk_confidence: confidence || null
    }
  });
  return NextResponse.json({ success: true, decision });
}
