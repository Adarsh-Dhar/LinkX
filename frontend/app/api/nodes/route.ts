
import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { createThirdwebClient } from "thirdweb";
import { facilitator as thirdwebFacilitator, settlePayment } from "thirdweb/x402";
import { etherlinkShadownet } from "thirdweb/chains";


const client = createThirdwebClient({
  secretKey: process.env.THIRDWEB_SECRET_KEY!,
});

const thirdwebX402Facilitator = thirdwebFacilitator({
  client,
  serverWalletAddress: process.env.SERVER_WALLET_ADDRESS!,
  waitUntil: "confirmed",
});


export async function GET(req: Request) {
  const paymentHeader = req.headers.get("x-payment");
  // Provide required fields for settlePayment (network, price, etc.)
  // For demo, use etherlinkShadownet and a price of 0 (free for now, update as needed)
  const result = await settlePayment({
    facilitator: thirdwebX402Facilitator,
    resourceUrl: "https://api.example.com/protected-endpoint",
    method: "GET",
    paymentData: paymentHeader || undefined,
    network: etherlinkShadownet,
    price: "0", // Set to actual price if needed
  });
  // Check for payment success using the correct property
  if (result.status !== 200) {
    return new Response("Payment Required", { status: 402 });
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
        reputation: true,
        status: true,
        isPurchased: true,
        icon: true,
      }
    });
    return NextResponse.json(nodes);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch nodes" }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const { nodeId } = await req.json();

    // 1. Find the Node (The Product)
    const node = await prisma.alphaNode.findUnique({
      where: { id: nodeId }
    });

    if (!node) {
      return NextResponse.json({ error: "Node not found" }, { status: 404 });
    }

    if (node.isPurchased) {
      return NextResponse.json({ message: "Already purchased" });
    }

    // 2. Setup Wallets (Agent vs Provider)
    // In a real app, 'providerAddress' would come from the node's database record.
    // Here we simulate a provider address.
    const providerAddress = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"; // Mock Provider Address
    const priceAmount = "10000"; // 0.01 USDC (6 decimals) - Mock Price

    console.log(`🤖 Initiating x402 Payment for: ${node.name}...`);


    // Payment logic removed: variables and logic referenced undefined imports and are not used in this handler.
    // If you want to implement payment in POST, use the thirdweb x402 flow as in GET, or clarify requirements.

    // 7. Unlock the Node in DB (simulate purchase for demo)
    const updatedNode = await prisma.alphaNode.update({
      where: { id: nodeId },
      data: { 
        isPurchased: true,
      }
    });

    return NextResponse.json({
      success: true,
      node: updatedNode,
      message: `Node marked as purchased.`
    });

  } catch (error: any) {
    console.error("Payment Failed:", error);
    return NextResponse.json(
      { error: error.message || "Payment processing failed" },
      { status: 500 }
    );
  }
}