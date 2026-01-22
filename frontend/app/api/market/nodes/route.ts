import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { Facilitator, CronosNetwork } from '@crypto.com/facilitator-client';
import { ethers } from 'ethers';

console.log("🔹 LOADED ROUTE: Dynamic Price + Hash Fix");

// --- CONFIGURATION ---
const AGENT_PRIVATE_KEY = process.env.AGENT_PRIVATE_KEY || "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"; 
const RPC_URL = "https://evm-t3.cronos.org"; // Cronos Testnet

// Data Provider Wallet
const PROVIDER_ADDRESS = "0xFe5e03799Fe833D93e950d22406F9aD901Ff3Bb9";

const facilitator = new Facilitator({
  network: CronosNetwork.CronosTestnet 
});

export async function GET() {
  try {
    const nodes = await prisma.alphaNode.findMany({ orderBy: { price: 'asc' } });
    return NextResponse.json(nodes);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch nodes" }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const nodeId = body.nodeId;

    if (!nodeId) return NextResponse.json({ error: "Missing nodeId" }, { status: 400 });

    const node = await prisma.alphaNode.findUnique({ where: { id: nodeId } });
    if (!node) return NextResponse.json({ error: "Node not found" }, { status: 404 });
    
    // Allow re-purchase simulation if needed, but typically:
    if (node.isPurchased) {
       // Only return "already purchased" if you want to block duplicate buys
       // return NextResponse.json({ success: true, message: "Already purchased", txHash: "PREVIOUSLY_BOUGHT" });
    }

    // --- 1. CALCULATE PRICE (1 tCRO = 100 USDC) ---
    const usdcPrice = Number(node.price || 0); 
    const conversionRate = 100;
    const croAmount = usdcPrice / conversionRate;
    
    // FIX: Limit decimals to avoid "underflow" or "too many decimals" error
    const safeCroString = croAmount.toFixed(18); 
    const valueInWei = ethers.parseEther(safeCroString).toString();

    console.log(`🤖 Paying for ${node.name} (${safeCroString} tCRO)`);

    // --- 2. PAYMENT EXECUTION ---
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    const signer = new ethers.Wallet(AGENT_PRIVATE_KEY, provider);
    
    const paymentHeader = await facilitator.generatePaymentHeader({
      to: PROVIDER_ADDRESS,
      value: valueInWei,
      signer: signer,
      validBefore: Math.floor(Date.now() / 1000) + 3600, 
    });

    const requirements = facilitator.generatePaymentRequirements({
      payTo: PROVIDER_ADDRESS,
      description: `Access to ${node.name}`,
      maxAmountRequired: valueInWei, 
    });

    const verifyBody = facilitator.buildVerifyRequest(paymentHeader, requirements);
    const verification = await facilitator.verifyPayment(verifyBody);

    if (!verification.isValid) {
      throw new Error(`Verification Failed: ${verification.invalidReason || 'Unknown'}`);
    }

    const settlement = await facilitator.settlePayment(verifyBody);
    
    // --- 3. ROBUST HASH EXTRACTION ---
    // Try all common property names for the hash
    // @ts-ignore
    const finalHash = settlement.hash || settlement.transactionHash || settlement.txHash || "HASH_NOT_FOUND";
    
    console.log(`🚀 Payment Settled! Hash: ${finalHash}`);

    // --- 4. DB UPDATE ---
    const updated = await prisma.alphaNode.update({
      where: { id: nodeId },
      data: { isPurchased: true }
    });

    return NextResponse.json({ 
      success: true, 
      node: updated,
      amountPaid: `${safeCroString} tCRO`,
      txHash: finalHash 
    });

  } catch (error: any) {
    console.error("❌ Purchase Failed:", error);
    return NextResponse.json({ 
      error: error.message || "Payment processing failed",
      details: String(error)
    }, { status: 500 });
  }
}