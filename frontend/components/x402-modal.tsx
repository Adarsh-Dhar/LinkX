"use client"

import { useState } from "react"
import { X, Zap } from "lucide-react"

interface Product {
  id: string
  name: string
  price: string
  provider: string
}

interface X402ModalProps {
  product: Product
  onClose: () => void
}

export default function X402Modal({ product, onClose }: X402ModalProps) {
  const [isProcessing, setIsProcessing] = useState(false)

  const handlePayment = () => {
    setIsProcessing(true)
    setTimeout(() => {
      alert(`Payment of ${product.price} USDC confirmed for ${product.name}!`)
      setIsProcessing(false)
      onClose()
    }, 2000)
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="glass border border-accent/50 rounded-lg max-w-md w-full mx-4 p-8 glow-accent">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-foreground">HTTP 402</h2>
            <p className="text-sm text-muted-foreground">Payment Required</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-card/50 rounded-lg transition-all">
            <X size={20} className="text-muted-foreground" />
          </button>
        </div>

        <div className="space-y-4 mb-6">
          <div className="border-b border-border/30 pb-4">
            <p className="text-xs text-muted-foreground mb-1">Product</p>
            <p className="font-mono text-foreground">{product.name}</p>
          </div>

          <div className="border-b border-border/30 pb-4">
            <p className="text-xs text-muted-foreground mb-1">Amount</p>
            <p className="text-2xl font-bold text-secondary">{product.price} USDC</p>
          </div>

          <div className="border-b border-border/30 pb-4">
            <p className="text-xs text-muted-foreground mb-1">Recipient Address</p>
            <p className="font-mono text-foreground text-sm">0x999...7d3a</p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground mb-1">Protocol</p>
            <p className="font-mono text-secondary">x402 Payment Protocol</p>
          </div>
        </div>

        <button
          onClick={handlePayment}
          disabled={isProcessing}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-gradient-to-r from-primary to-accent hover:shadow-lg hover:shadow-primary/30 disabled:opacity-50 transition-all text-white font-semibold"
        >
          <Zap size={18} />
          {isProcessing ? "Processing..." : "Sign & Pay"}
        </button>

        <p className="text-xs text-muted-foreground mt-4 text-center">
          Your wallet will be prompted to confirm the transaction
        </p>
      </div>
    </div>
  )
}
