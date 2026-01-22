import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { Facilitator, CronosNetwork } from '@crypto.com/facilitator-client';
import { ethers } from 'ethers';

// 1. Configuration
// Ideally, put these in your .env file
const AGENT_PRIVATE_KEY = process.env.AGENT_PRIVATE_KEY; // Default: Hardhat Account #0 (CHANGE THIS FOR REAL NETWORKS)
const RPC_URL = "https://evm-t3.cronos.org"; // Cronos Testnet

// Initialize Facilitator
const facilitator = new Facilitator({
  network: CronosNetwork.CronosTestnet 
});

export async function GET() {
  try {
    const nodes = await prisma.alphaNode.findMany({
      orderBy: { name: 'asc' }
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

    if (!AGENT_PRIVATE_KEY) {
      throw new Error("AGENT_PRIVATE_KEY is not set in environment variables.");
    }

    // 3. Initialize Agent's Wallet (The Buyer)
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    const signer = new ethers.Wallet(AGENT_PRIVATE_KEY, provider);

    // 4. x402 Step A: Generate Payment Header (Buyer signs the promise to pay)
    // This creates an EIP-3009 authorization signature
    const paymentHeader = await facilitator.generatePaymentHeader({
      to: providerAddress,
      value: priceAmount,
      signer: signer,
      validBefore: Math.floor(Date.now() / 1000) + 3600, // Valid for 1 hour
    });

    console.log("✅ Payment Header Signed");

    // 5. x402 Step B: Generate Requirements (Seller's Terms)
    const requirements = facilitator.generatePaymentRequirements({
      payTo: providerAddress,
      description: `Access to ${node.name}`,
      maxAmountRequired: priceAmount,
    });

    // 6. x402 Step C: Verify & Settle (Facilitator Execution)
    const verifyBody = facilitator.buildVerifyRequest(paymentHeader, requirements);
    
    // Check if valid
    const verification = await facilitator.verifyPayment(verifyBody);
    if (!verification.isValid) {
      throw new Error(`x402 Verification Failed: ${verification.invalidReason}`);
    }

    console.log("✅ Payment Verified by Facilitator. Settling...");

    // Settle (Broadcast to Blockchain)
    const settlement = await facilitator.settlePayment(verifyBody);
    
    console.log(`🚀 Payment Settled! Tx Hash: ${settlement.txHash}`);

    // 7. Payment Success! Unlock the Node in DB
    const updatedNode = await prisma.alphaNode.update({
      where: { id: nodeId },
      data: { 
        isPurchased: true,
        // Optional: Save tx hash if you add a column for it
        // lastTxHash: settlement.transactionHash 
      }
    });

    return NextResponse.json({
      success: true,
      node: updatedNode,
      txHash: settlement.txHash,
      message: `Successfully paid provider via x402. Transaction: ${settlement.txHash}`
    });

  } catch (error: any) {
    console.error("Payment Failed:", error);
    return NextResponse.json(
      { error: error.message || "Payment processing failed" },
      { status: 500 }
    );
  }
}