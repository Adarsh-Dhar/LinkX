import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// Simulate data for different node types
function generateSimulatedData(category: string) {
  switch (category) {
    case 'Sentiment':
      // Simulate sentiment score between -1 and 1
      return { sentiment: (Math.random() * 2 - 1).toFixed(3) };
    case 'Volatility':
      // Simulate volatility as a random walk
      return { volatility: (Math.random() * 0.2 + 0.8).toFixed(3) };
    default:
      return { value: Math.random().toFixed(3) };
  }
}

export async function GET(req: NextRequest, { params }: { params: { nodeId: string } }) {
  const nodeId = params.nodeId;
  const apiKey = req.headers.get('x402-access-key');

  // Fetch node from DB
  const node = await prisma.alphaNode.findUnique({ where: { id: nodeId } });
  if (!node) {
    return NextResponse.json({ error: 'Node not found' }, { status: 404 });
  }

  // Gatekeeping: check if purchased and API key matches
  if (!node.isPurchased || !node.apiKey || node.apiKey !== apiKey) {
    return NextResponse.json({ error: 'Payment Required' }, { status: 402 });
  }

  // Simulate data
  const data = generateSimulatedData(node.category);
  return NextResponse.json({ nodeId, data });
}
