import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { Facilitator, CronosNetwork } from '@crypto.com/facilitator-client';
import { ethers } from 'ethers';

console.log("🔹 LOADED ROUTE: Ultimate Hash Finder");

const AGENT_PRIVATE_KEY = process.env.AGENT_PRIVATE_KEY;
const RPC_URL = "https://evm-t3.cronos.org"; 
const PROVIDER_ADDRESS = "0xFe5e03799Fe833D93e950d22406F9aD901Ff3Bb9";

export async function POST(req: Request) {
  try {
    // ... (Validation logic stays the same) ...
    const body = await req.json();
    const nodeId = body.nodeId;
    if (!nodeId) return NextResponse.json({ error: "Missing nodeId" }, { status: 400 });

    const node = await prisma.alphaNode.findUnique({ where: { id: nodeId } });
    if (!node) return NextResponse.json({ error: "Node not found" }, { status: 404 });

    // 1. Setup your Wallet
    if (!AGENT_PRIVATE_KEY) throw new Error("AGENT_PRIVATE_KEY is missing");
    
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    const signer = new ethers.Wallet(AGENT_PRIVATE_KEY, provider);

    // 2. Initialize Facilitator
    // (You don't need to pass the key here if you pass the signer later)
    const facilitator = new Facilitator({
      network: CronosNetwork.CronosTestnet
    });

    // 3. Price Logic
    const usdcPrice = Number(node.price || 0); 
    const valueInWei = ethers.parseEther((usdcPrice / 100).toFixed(18)).toString();

    console.log(`🤖 Paying for ${node.name} with wallet: ${signer.address}`);

    // 4. Generate Payment Intent (Signed by YOU)
    const paymentHeader = await facilitator.generatePaymentHeader({
      to: PROVIDER_ADDRESS,
      value: valueInWei,
      signer: signer, // <--- This signs the "Check"
      validBefore: Math.floor(Date.now() / 1000) + 3600, 
    });

    const requirements = facilitator.generatePaymentRequirements({
      payTo: PROVIDER_ADDRESS,
      description: `Access to ${node.name}`,
      maxAmountRequired: valueInWei, 
    });

    const verifyBody = facilitator.buildVerifyRequest(paymentHeader, requirements);
    
    // 5. Broadcast the Transaction (The Critical Fix)
    console.log("⏳ Broadcasting transaction...");

    // ✅ FIX: Pass 'signer' as the 2nd argument so YOUR wallet pays the gas.
    // @ts-ignore
    const settlement = await facilitator.settlePayment(verifyBody, signer);
    console.log("✅ Payment Settled:", settlement);
    
    // ... (Rest of your logging and DB update logic) ...

    // Robust Hash Extraction
    let finalHash = null;
    console.log("Settlement Object:", settlement);
    if (settlement) {
      if (typeof settlement === 'string') {
        // If settlement is a string, check if it's a hash
        if (/^0x([A-Fa-f0-9]{64})$/.test(settlement)) {
          finalHash = settlement;
        } else {
          // Try to parse as JSON if possible
          try {
            const parsed = JSON.parse(settlement);
            finalHash = parsed.hash || parsed.transactionHash || parsed.txHash || null;
          } catch {}
        }
      } else if (typeof settlement === 'object') {
        finalHash = settlement.txHash || null;
        // Sometimes the hash is nested in a receipt
        if (!finalHash && settlement.txHash) {
          finalHash = settlement.txHash || null;
        }
      }
    }
    return NextResponse.json({ 
      success: true, 
      node: node, // update this to use the real updated node
      txHash: finalHash || "HASH_NOT_FOUND"
    });

  } catch (error: any) {
    console.error("❌ Purchase Failed:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}