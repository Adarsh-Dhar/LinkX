import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

export async function GET() {
  // Get the 50 most recent DataLog entries
  const logs = await prisma.dataLog.findMany({
    orderBy: { fetchedAt: 'desc' },
    take: 50,
  });
  return NextResponse.json({
    dataLog: logs.map(l => ({
      fetchedAt: l.fetchedAt,
      normalized: l.normalized,
      data: l.data
    }))
  });
}
