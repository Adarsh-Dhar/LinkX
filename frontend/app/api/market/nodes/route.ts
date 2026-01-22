import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { Facilitator, CronosNetwork } from '@crypto.com/facilitator-client';
import { ethers } from 'ethers';

console.log("🔹 LOADED X402 PAYMENT ROUTE");

// --- CONFIGURATION ---
const AGENT_PRIVATE_KEY = process.env.AGENT_PRIVATE_KEY || "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"; 
const RPC_URL = "https://evm-t3.cronos.org"; // Cronos Testnet

const facilitator = new Facilitator({
  network: CronosNetwork.CronosTestnet 
});

// GET /api/market/nodes
export async function GET() {
  try {
    const nodes = await prisma.alphaNode.findMany({ orderBy: { price: 'asc' } });
    return NextResponse.json(nodes);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch nodes" }, { status: 500 });
  }
}

// POST /api/market/nodes - EXECUTES PAYMENT
export async function POST(req: Request) {
  try {
    const body = await req.json();
    const nodeId = body.nodeId;

    if (!nodeId) return NextResponse.json({ error: "Missing nodeId" }, { status: 400 });

    // 1. Fetch Node
    const node = await prisma.alphaNode.findUnique({ where: { id: nodeId } });
    if (!node) return NextResponse.json({ error: "Node not found" }, { status: 404 });
    if (node.isPurchased) {
      return NextResponse.json({ success: true, message: "Already purchased", txHash: "PREVIOUSLY_BOUGHT" });
    }

    console.log(`🤖 Processing x402 Payment for: ${node.name}`);

    // --- PAYMENT LOGIC ---
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    const signer = new ethers.Wallet(AGENT_PRIVATE_KEY, provider);
    
    // Mock Provider Address & Price
    const providerAddress = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"; 
    const priceAmount = "10000"; // 0.01 USDC

    const paymentHeader = await facilitator.generatePaymentHeader({
      to: providerAddress,
      value: priceAmount,
      signer: signer,
      validBefore: Math.floor(Date.now() / 1000) + 3600, 
    });

    const requirements = facilitator.generatePaymentRequirements({
      payTo: providerAddress,
      description: `Access to ${node.name}`,
      maxAmountRequired: priceAmount,
    });

    const verifyBody = facilitator.buildVerifyRequest(paymentHeader, requirements);
    const verification = await facilitator.verifyPayment(verifyBody);

    if (!verification.isValid) throw new Error(`Verification Failed: ${verification.invalidReason || 'Unknown'}`);

    // Settle
    const settlement = await facilitator.settlePayment(verifyBody);
    console.log(`🚀 Payment Settled! Hash: ${settlement.txHash}`);

    // --- DB UPDATE ---
    const updated = await prisma.alphaNode.update({
      where: { id: nodeId },
      data: { isPurchased: true }
    });

    // --- RETURN THE HASH ---
    return NextResponse.json({ 
      success: true, 
      node: updated,
      txHash: settlement.txHash 
    });

  } catch (error: any) {
    console.error("❌ Purchase Failed:", error);
    return NextResponse.json({ 
      error: error.message || "Payment processing failed",
      details: String(error)
    }, { status: 500 });
  }
}