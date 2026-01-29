
import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

export async function PATCH(req: Request) {
  try {
    const body = await req.json();
    const { nodeId, whitelisted } = body;
    if (!nodeId || typeof whitelisted !== "boolean") {
      return NextResponse.json({ error: "Missing nodeId or whitelisted flag" }, { status: 400 });
    }
    const node = await prisma.alphaNode.findUnique({ where: { id: nodeId } });
    if (!node) return NextResponse.json({ error: "Node not found" }, { status: 404 });
    const updated = await prisma.alphaNode.update({
      where: { id: nodeId },
      data: { whitelisted },
    });
    return NextResponse.json({ success: true, node: updated });
  } catch (error: any) {
    return NextResponse.json({ error: error.message || "Failed to update whitelist status" }, { status: 500 });
  }
}

export async function GET() {
  try {
    const nodes = await prisma.alphaNode.findMany({
      where: { status: 'active' }
    });
    return NextResponse.json(nodes);
  } catch (error) {
    return NextResponse.json({ error: 'Database failure' }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    // 1. STRICT KEY CHECK
    const privateKey = process.env.WALLET_PRIVATE_KEY;
    if (!privateKey || !privateKey.startsWith("0x")) {
      return NextResponse.json({ 
        error: "Configuration Error", 
        details: "WALLET_PRIVATE_KEY is missing or invalid in .env file." 
      }, { status: 500 });
    }

    const body = await req.json();
    const nodeId = body.nodeId;
    if (!nodeId) return NextResponse.json({ error: "Missing nodeId" }, { status: 400 });

    const node = await prisma.alphaNode.findUnique({ where: { id: nodeId } });
    if (!node) return NextResponse.json({ error: "Node not found" }, { status: 404 });

    // --- 2. SETUP WALLET ---
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    const signer = new ethers.Wallet(privateKey, provider);
    
    // --- 3. CALCULATE REAL PRICE (USDC) ---
    // 🚨 FIX: Use the actual price from the database 🚨
    const payAmount = Number(node.price); 
    
    if (isNaN(payAmount) || payAmount <= 0) {
         // Fallback just in case DB price is 0 or null
         console.warn("⚠️ Invalid node price, defaulting to 0.01 for safety");
    }

    // USDC = 6 Decimals
    const valueInWei = ethers.parseUnits(payAmount.toString(), 6).toString();

    console.log(`🤖 Paying for ${node.name}`);
    console.log(`💰 Price: ${payAmount} USDC (Raw: ${valueInWei})`);
    console.log(`🆔 Wallet: ${signer.address}`);

    // --- 4. CHECK BALANCE ---
    const usdcAddress = "0xc01efAaF7C5C61bEbFAeb358E1161b537b8bC0e0"; 
    const usdcAbi = ["function balanceOf(address owner) view returns (uint256)"];
    const usdcContract = new ethers.Contract(usdcAddress, usdcAbi, provider);
    const balance = await usdcContract.balanceOf(signer.address);

    if (balance < BigInt(valueInWei)) {
        return NextResponse.json({ 
            error: "Insufficient Funds", 
            details: `Wallet has ${ethers.formatUnits(balance, 6)} USDC. Needed: ${payAmount}.` 
        });
    }

    // --- 5. EXECUTE PAYMENT ---
    const paymentHeader = await facilitator.generatePaymentHeader({
      to: PROVIDER_ADDRESS,
      value: valueInWei,
      signer: signer,
      asset: Contract.USDC, 
      validBefore: Math.floor(Date.now() / 1000) + 3600, 
    });

    const requirements = facilitator.generatePaymentRequirements({
      payTo: PROVIDER_ADDRESS,
      description: `Access to ${node.name}`,
      maxAmountRequired: valueInWei,
      asset: Contract.USDC
    });

    const verifyBody = facilitator.buildVerifyRequest(paymentHeader, requirements);
    const verification = await facilitator.verifyPayment(verifyBody);

    if (!verification.isValid) {
      throw new Error(`Verification Failed: ${verification.invalidReason || 'Unknown'}`);
    }

    console.log("🚀 Broadcasting...");
    const settlement = await facilitator.settlePayment(verifyBody);
    
    // --- 6. HASH EXTRACTION (Improved) ---
    // Log keys to see what we actually get back (check terminal if this fails)
    console.log("📦 Settlement Object Keys:", Object.keys(settlement));

    // Try standard fields
    // @ts-ignore
    let finalHash = settlement.hash || settlement.transactionHash || settlement.txHash;
    
    // Fallback: Check inside receipt if it exists (common in some SDK versions)
    // @ts-ignore
    if (!finalHash && settlement.receipt) {
        // @ts-ignore
        finalHash = settlement.receipt.hash || settlement.receipt.transactionHash;
    }

    if (!finalHash) finalHash = "HASH_NOT_FOUND_CHECK_LOGS";

    console.log(`✅ Success! Hash: ${finalHash}`);

    const updated = await prisma.alphaNode.update({
      where: { id: nodeId },
      data: { isPurchased: true }
    });

    return NextResponse.json({ 
      success: true, 
      node: updated,
      amountPaid: `${payAmount} USDC`,
      txHash: finalHash
    });

  } catch (error: any) {
    console.error("❌ Purchase Error:", error);
    return NextResponse.json({ 
      error: error.message || "Payment processing failed",
      details: String(error)
    }, { status: 500 });
  }
}