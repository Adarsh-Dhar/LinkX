
"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Lock, Unlock, Loader2, CheckCircle, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { ethers } from "ethers"
import { Facilitator, CronosNetwork } from '@crypto.com/facilitator-client';


interface Product {
  id: string;
  name: string;
  description: string;
  price: string;
  category?: string;
  isPurchased?: boolean;
  provider?: string;
  status?: "locked" | "unlocked";
  bullish?: number;
}


export default function AlphaProductCard({ product }: { product: Product }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [purchased, setPurchased] = useState(product.isPurchased || product.status === "unlocked");
  const isLocked = !purchased;

  // Card click handler (except button)
  const handleCardClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // Prevent navigation if the click is on the purchase button or inside it
    if ((e.target as HTMLElement).closest("button")) return;
    router.push(`/market/${product.id}`);
  };

  const handlePurchase = async () => {
    setLoading(true)
    try {
      // --- 1. CONNECT TO WALLET (METAMASK) ---
      const ethereum = (window as any).ethereum;
      if (!ethereum) {
        throw new Error("Please install MetaMask to purchase.");
      }
      const provider = new ethers.BrowserProvider(ethereum);
      const signer = await provider.getSigner();
      const userAddress = await signer.getAddress();
      console.log(`💳 Connected: ${userAddress}`);
      toast.info("Wallet connected. Preparing payment...");

      // --- 2. INITIALIZE FACILITATOR (CLIENT-SIDE) ---
      // We pass the 'signer' so the library can request signatures and transactions from MetaMask
      const facilitator = new Facilitator({
        network: CronosNetwork.CronosTestnet,
        signer: signer
      } as any);

      // --- 3. PREPARE PAYMENT DATA ---
      const usdcPrice = Number(product.price || 0);
      const safeWxtzString = (usdcPrice / 100).toFixed(18); // Example conversion logic
      const valueInWei = ethers.parseEther(safeWxtzString).toString();
      const PROVIDER_ADDRESS = "0xFe5e03799Fe833D93e950d22406F9aD901Ff3Bb9";

      // --- 4. SIGN PAYMENT INTENT (EIP-712) ---
      toast.loading("Please sign the payment authorization...");
      const paymentHeader = await facilitator.generatePaymentHeader({
        to: PROVIDER_ADDRESS,
        value: valueInWei,
        signer: signer, // User signs here
        validBefore: Math.floor(Date.now() / 1000) + 3600, 
      });

      const requirements = facilitator.generatePaymentRequirements({
        payTo: PROVIDER_ADDRESS,
        description: `Access to ${product.name}`,
        maxAmountRequired: valueInWei, 
      });

      const verifyBody = facilitator.buildVerifyRequest(paymentHeader, requirements);

      // --- 5. EXECUTE TRANSACTION (User pays Gas) ---
      toast.loading("Broadcasting transaction... Check MetaMask.");
      // @ts-ignore: Pass signer to force library to use MetaMask for broadcasting
      const settlement = await facilitator.settlePayment(verifyBody, signer);

      // Extract Hash Robustly
      // @ts-ignore
      let txHash = settlement.hash || settlement.transactionHash || settlement.txHash;
      if (!txHash && typeof settlement === 'string') txHash = settlement;

      if (!txHash) {
        console.error("Settlement debug:", settlement);
        throw new Error("Transaction failed or hash missing.");
      }

      console.log(`🚀 Payment Sent! Hash: ${txHash}`);
      toast.success("Payment successful! Verifying with server...");

      // --- 6. SEND PROOF TO BACKEND ---
      // We send the txHash so the server can verify and unlock the node
      const res = await fetch("/api/market/nodes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          nodeId: product.id, 
          txHash: txHash 
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Server verification failed");

      setPurchased(true);
      toast.success(`Unlocked: ${product.name}`);

    } catch (error: any) {
      console.error("Purchase Error:", error);
      // Handle specific MetaMask errors (like user rejection)
      if (error.code === 'ACTION_REJECTED' || error.code === 4001) {
        toast.error("Transaction rejected by user.");
      } else {
        toast.error(error.message || "Purchase failed. See console.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className={`relative flex flex-col transition-all hover:border-primary/50 ${purchased ? "border-green-500/50 bg-green-500/5" : ""} glass glow-primary p-6 rounded-lg border border-border/30 h-full cursor-pointer`}
      onClick={handleCardClick}
      tabIndex={0}
      role="button"
      aria-label={`View details for ${product.name}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-foreground flex items-center gap-2">{product.name} {purchased && <CheckCircle className="h-5 w-5 text-green-500" />}</h3>
          {product.provider && <p className="text-xs text-muted-foreground mt-1">{product.provider}</p>}
        </div>
        {isLocked ? <Lock className="text-accent" size={20} /> : <Unlock className="text-secondary" size={20} />}
      </div>

      <p className="text-sm text-muted-foreground mb-4 flex-1">{product.description}</p>

      {!isLocked && product.bullish !== undefined && (
        <div className="mb-4 p-3 bg-black/40 rounded-lg border border-secondary/30">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground">Bullish Sentiment</span>
            <span className="text-sm font-bold text-secondary">{product.bullish}%</span>
          </div>
          <div className="w-full h-2 bg-black/80 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-secondary to-primary"
              style={{ width: `${product.bullish}%` }}
            ></div>
          </div>
          <p className="text-xs text-secondary mt-2 font-mono">Action: ACCUMULATE</p>
        </div>
      )}

      <div className="flex items-center justify-between gap-2">
        <span className="text-lg font-bold text-foreground">{product.price} USDC</span>
        <Button
          onClick={e => {
            e.stopPropagation();
            handlePurchase();
          }}
          disabled={loading || purchased}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            isLocked
              ? "bg-gradient-to-r from-primary to-accent hover:shadow-lg hover:shadow-primary/30 text-white"
              : "bg-green-500/20 text-green-400 border border-green-500/30"
          }`}
          variant={purchased ? "outline" : "default"}
          size="lg"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : purchased ? (
            <>
              <Unlock className="mr-2 h-4 w-4" />
              Access Data
            </>
          ) : (
            <>
              <Lock className="mr-2 h-4 w-4" />
              Purchase Access
            </>
          )}
        </Button>
        <Button
          variant="secondary"
          className="px-4 py-2 rounded-lg text-sm font-medium"
          onClick={e => {
            e.stopPropagation();
            router.push(`/market/${product.id}`);
          }}
        >
          Details
        </Button>
      </div>
    </div>
  );
}
