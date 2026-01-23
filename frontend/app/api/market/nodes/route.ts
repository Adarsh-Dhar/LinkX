import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { Facilitator, CronosNetwork } from '@crypto.com/facilitator-client';
import { ethers } from 'ethers';

console.log("🔹 LOADED ROUTE: Ultimate Hash Finder");

const AGENT_PRIVATE_KEY = process.env.AGENT_PRIVATE_KEY;
const RPC_URL = "https://evm-t3.cronos.org"; 

const PROVIDER_ADDRESS = "0xFe5e03799Fe833D93e950d22406F9aD901Ff3Bb9";

// GET /api/market/nodes - Returns all AlphaNode records
export async function GET() {
  try {
    const nodes = await prisma.alphaNode.findMany();
    return NextResponse.json(nodes);
  } catch (error: any) {
    return NextResponse.json({ error: error.message || "Failed to fetch nodes" }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const nodeId = body.nodeId;

    if (!nodeId) return NextResponse.json({ error: "Missing nodeId" }, { status: 400 });

    const node = await prisma.alphaNode.findUnique({ where: { id: nodeId } });
    if (!node) return NextResponse.json({ error: "Node not found" }, { status: 404 });

    // --- 1. SETUP WALLET ---
    if (!AGENT_PRIVATE_KEY) throw new Error("AGENT_PRIVATE_KEY is missing");
    
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    const signer = new ethers.Wallet(AGENT_PRIVATE_KEY, provider);

    console.log(`💳 Wallet Loaded: ${signer.address}`);

    // --- 2. INITIALIZE FACILITATOR ---
    const facilitator = new Facilitator({
      network: CronosNetwork.CronosTestnet
    });

    // --- 3. 🚨 FORCE INJECTION (The Fix) 🚨 ---
    // The library ignores arguments in settlePayment() and uses internal state.
    // We force your wallet into the instance properties here.
    
    // @ts-ignore
    facilitator.signer = signer;
    // @ts-ignore
    facilitator.privateKey = AGENT_PRIVATE_KEY; 
    // @ts-ignore
    facilitator.wallet = signer; // Backup property name used by some versions

    // --- 4. PREPARE PAYMENT ---
    const usdcPrice = Number(node.price || 0); 
    const valueInWei = ethers.parseEther((usdcPrice / 100).toFixed(18)).toString();

    console.log(`🤖 Paying for ${node.name} (${valueInWei} wei)`);

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
    
    // --- 5. SETTLE PAYMENT ---
    console.log("⏳ Broadcasting transaction...");

    // Now call settlePayment without arguments (it will use the injected signer)
    // @ts-ignore
    const settlement = await facilitator.settlePayment(verifyBody);
    
    console.log("✅ Settlement Response:", JSON.stringify(settlement, null, 2));

    // --- 6. HASH EXTRACTION ---
    let finalHash = null;
    if (settlement) {
      if (typeof settlement === 'string') {
        if (/^0x([A-Fa-f0-9]{64})$/.test(settlement)) finalHash = settlement;
      } else if (typeof settlement === 'object') {
        // @ts-ignore
        finalHash = settlement.hash || settlement.transactionHash || settlement.txHash;
        // @ts-ignore
        if (!finalHash && settlement.transaction) finalHash = settlement.transaction.hash;
      }
    }

    if (!finalHash || finalHash === "HASH_NOT_FOUND" || finalHash === "MANUAL_CHECK_REQUIRED") {
      return NextResponse.json({ 
        error: "Transaction hash not found. Payment not completed.", 
        debug: settlement 
      }, { status: 500 });
    }

    // --- 7. UPDATE DB ---
    await prisma.alphaNode.update({
      where: { id: nodeId },
      data: { isPurchased: true }
    });

    return NextResponse.json({ 
      success: true, 
      node: node, 
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