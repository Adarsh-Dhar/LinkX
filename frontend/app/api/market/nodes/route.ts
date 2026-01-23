import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  try {
    const nodes = await prisma.alphaNode.findMany({ orderBy: { price: 'asc' } });
    return NextResponse.json(nodes);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch nodes" }, { status: 500 });
  }
}

// ✅ NEW: Receives payment proof from Frontend
export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { nodeId, txHash } = body;

    if (!nodeId) return NextResponse.json({ error: "Missing nodeId" }, { status: 400 });

    // 1. If we received a hash, the User already paid via MetaMask
    if (txHash) {
      console.log(`✅ User verified payment for Node ${nodeId}. Hash: ${txHash}`);
      
      const updated = await prisma.alphaNode.update({
        where: { id: nodeId },
        data: { isPurchased: true }
      });

      return NextResponse.json({ success: true, node: updated, txHash });
    }

    return NextResponse.json({ error: "Transaction hash missing. Please pay via wallet." }, { status: 400 });

  } catch (error: any) {
    console.error("❌ Purchase Verification Failed:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}