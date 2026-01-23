
"use client"

import { useState } from "react"
import { Lock, Unlock, Loader2, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { ethers } from "ethers"
import { Facilitator, CronosNetwork } from '@crypto.com/facilitator-client';

interface Product {
  id: string
  name: string
  price: string
  provider: string
  status: "locked" | "unlocked"
  description: string
  bullish: number
  isPurchased?: boolean
}

export default function AlphaProductCard({ product }: { product: Product }) {
  const [loading, setLoading] = useState(false)
  const [purchased, setPurchased] = useState(product.isPurchased || product.status === "unlocked")
  const isLocked = !purchased

  const handlePurchase = async () => {
    setLoading(true);
    try {
      // 1. Connect to MetaMask
      if (typeof window === "undefined" || !(window as any).ethereum) {
        throw new Error("Please install MetaMask to purchase data nodes.");
      }
      // Type for window.ethereum
      const eth = (window as any).ethereum;
      const provider = new ethers.BrowserProvider(eth);
      const signer = await provider.getSigner();

      toast.info("Preparing transaction...");

      // 2. Initialize Facilitator (Client Side)
      const facilitator = new Facilitator({
        network: CronosNetwork.CronosTestnet,
      });

      // 3. Prepare Payment Details
      const usdcPrice = typeof product.price === "number" ? product.price : Number(product.price || 0);
      const safeCroString = (usdcPrice / 100).toFixed(18);
      const valueInWei = ethers.parseEther(safeCroString).toString();
      const PROVIDER_ADDRESS = "0xFe5e03799Fe833D93e950d22406F9aD901Ff3Bb9";

      // 4. Generate Payment Header (User Signs)
      toast.loading("Please sign the payment authorization...");
      const paymentHeader = await facilitator.generatePaymentHeader({
        to: PROVIDER_ADDRESS,
        value: valueInWei,
        signer,
        validBefore: Math.floor(Date.now() / 1000) + 3600,
      });

      const requirements = facilitator.generatePaymentRequirements({
        payTo: PROVIDER_ADDRESS,
        description: `Access to ${product.name}`,
        maxAmountRequired: valueInWei,
      });

      const verifyBody = facilitator.buildVerifyRequest(paymentHeader, requirements);

      // 5. Settle Payment (User Broadcasts & Pays Gas)
      toast.loading("Broadcasting transaction via MetaMask...");
      // @ts-expect-error: Facilitator type
      const settlement = await facilitator.settlePayment(verifyBody, signer);


      // Extract Hash robustly

      let txHash: string | undefined = undefined;
      if (typeof settlement === 'string') {
        // Sometimes the SDK returns the hash as a string
        if (/^0x([A-Fa-f0-9]{64})$/.test(settlement)) txHash = settlement;
      } else if (typeof settlement === 'object' && settlement !== null) {
        // Per X402SettleResponse, txHash is the correct property
        txHash = settlement.txHash;
      }

      if (!txHash) throw new Error("Transaction failed or hash not found.");

      // eslint-disable-next-line no-console
      console.log("🚀 Payment Sent! Hash:", txHash);
      toast.success("Payment confirmed! Unlocking node...");

      // 6. Notify Backend to Update DB
      const res = await fetch("/api/market/nodes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nodeId: product.id, txHash }),
      });

      if (!res.ok) throw new Error("Failed to verify purchase with server");

      setPurchased(true);
      toast.success(`Successfully acquired ${product.name}!`);
    } catch (error: any) {
      // eslint-disable-next-line no-console
      console.error(error);
      toast.error(error?.message || "Purchase failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass glow-primary p-6 rounded-lg border border-border/30 hover:border-primary/50 transition-all cursor-pointer h-full flex flex-col">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-foreground">{product.name}</h3>
          <p className="text-xs text-muted-foreground mt-1">{product.provider}</p>
        </div>
        {isLocked ? <Lock className="text-accent" size={20} /> : <Unlock className="text-secondary" size={20} />}
      </div>

      <p className="text-sm text-muted-foreground mb-4 flex-1">{product.description}</p>

      {!isLocked && (
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

      <div className="flex items-center justify-between">
        <span className="text-lg font-bold text-foreground">{product.price} USDC</span>
        <Button
          onClick={handlePurchase}
          disabled={loading || purchased}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            isLocked
              ? "bg-gradient-to-r from-primary to-accent hover:shadow-lg hover:shadow-primary/30 text-white"
              : "bg-green-500/20 text-green-400 border border-green-500/30"
          }`}
        >
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : isLocked ? "Purchase" : "Active"}
        </Button>
      </div>
    </div>
  )
}
