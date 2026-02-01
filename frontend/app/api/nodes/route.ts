
import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { createThirdwebClient } from 'thirdweb';
import { facilitator as thirdwebFacilitator, settlePayment } from 'thirdweb/x402';
import { etherlinkShadownet } from 'thirdweb/chains';


const client = createThirdwebClient({
  secretKey: process.env.THIRDWEB_SECRET_KEY!,
});

const thirdwebX402Facilitator = thirdwebFacilitator({
  client,
  serverWalletAddress: process.env.SERVER_WALLET_ADDRESS!,
  waitUntil: 'confirmed',
});


export async function GET(req: Request) {
  const paymentHeader = req.headers.get('x-payment');
  // Provide required fields for settlePayment (network, price, etc.)
  // Use minimum required price to satisfy validation requirements
  const result = await settlePayment({
    facilitator: thirdwebX402Facilitator,
    resourceUrl: 'https://api.example.com/protected-endpoint',
    method: 'GET',
    paymentData: paymentHeader || undefined,
    network: etherlinkShadownet,
    price: '0.0001', // Minimum amount required by Zod validation (at least 0.0001)
  });
  // Check for payment success using the correct property
  if (result.status !== 200) {
    return new Response('Payment Required', { status: 402 });
  }
  // ...your API logic here (example: fetch nodes)
  try {
    const nodes = await prisma.alphaNode.findMany({
      orderBy: { name: 'asc' },
      select: {
        id: true,
        name: true,
        category: true,
        description: true,
        price: true,
        // reputation: true,
        status: true,
        isPurchased: true,
        icon: true,
        // provider: true,
      },
    });
    return NextResponse.json(nodes);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch nodes' }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const { nodeId, typedData, signature } = await req.json();

    // 1. Find the Node (The Product)
    const node = await prisma.alphaNode.findUnique({
      where: { id: nodeId },
      select: {
        id: true,
        name: true,
        // provider: true,
        isPurchased: true,
        price: true,
      },
    });

    if (!node) {
      return NextResponse.json({ error: 'Node not found' }, { status: 404 });
    }

    if (node.isPurchased) {
      return NextResponse.json({ message: 'Already purchased' });
    }

    // 2. Setup payment details
    // const providerAddress = node.provider || '0x70997970C51812dc3A010C7d01b50e0d17dc79C8';
    const priceAmount = node.price?.toString() || '10000';

    // 3. Verify x402 payment using thirdweb
    const paymentResult = await settlePayment({
      facilitator: thirdwebX402Facilitator,
      resourceUrl: `http://localhost:4001/api/${node.id}`,
      method: 'GET',
      paymentData: JSON.stringify({ typedData, signature }),
      network: etherlinkShadownet,
      price: priceAmount,
    });

    if (paymentResult.status !== 200) {
      return NextResponse.json({ error: 'Payment verification failed' }, { status: 402 });
    }

    // 4. Unlock the Node in DB
    const updatedNode = await prisma.alphaNode.update({
      where: { id: nodeId },
      data: {
        isPurchased: true,
      },
    });

    return NextResponse.json({
      success: true,
      node: updatedNode,
      message: 'Node marked as purchased.',
    });
  } catch (error: any) {
    console.error('Payment Failed:', error);
    return NextResponse.json(
      { error: error.message || 'Payment processing failed' },
      { status: 500 }
    );
  }
}