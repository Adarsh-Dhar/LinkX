import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

// GET /api/market/nodes
export async function GET() {
  try {
    // 1. Fetch all nodes from SQLite
    const nodes = await prisma.alphaNode.findMany({
      orderBy: {
        price: 'asc', // Show cheapest first
      },
    });

    // 2. Return as JSON
    return NextResponse.json(nodes);
  } catch (error) {
    console.error("Market API Error:", error);
    return NextResponse.json(
      { error: "Failed to fetch market nodes" }, 
      { status: 500 }
    );
  }
}

// POST /api/market/buy (Optional: For handling purchases later)
export async function POST(req: Request) {
  try {
    const { nodeId } = await req.json();
    
    // Mark as purchased in DB
    const updated = await prisma.alphaNode.update({
      where: { id: nodeId },
      data: { isPurchased: true }
    });

    return NextResponse.json({ success: true, node: updated });
  } catch (error) {
    return NextResponse.json({ error: "Purchase failed" }, { status: 500 });
  }
}
