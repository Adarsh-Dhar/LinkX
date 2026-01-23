import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

export async function GET() {
  // Get the 50 most recent DataLog entries, joined with AlphaNode name
  const logs = await prisma.dataLog.findMany({
    orderBy: { fetchedAt: 'desc' },
    take: 50,
    include: { node: { select: { name: true } } }
  });
  return NextResponse.json({
    dataLog: logs.map(l => ({
      fetchedAt: l.fetchedAt,
      nodeName: l.node?.name || l.nodeId,
      normalized: l.normalized,
      data: l.data
    }))
  });
}
