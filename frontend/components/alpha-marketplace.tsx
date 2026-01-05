"use client"

import { useState } from "react"
import AlphaProductCard from "./alpha-product-card"
import X402Modal from "./x402-modal"

export default function AlphaMarketplace() {
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null)
  const [showPaymentModal, setShowPaymentModal] = useState(false)

  const products = [
    {
      id: "whale-watcher",
      name: "VVS Whale Watcher",
      price: "0.10",
      provider: "HedgeFund_AI",
      status: "locked",
      description: "Monitor large whale movements on VVS",
      bullish: 75,
    },
    {
      id: "sentiment",
      name: "CRO Sentiment Analysis",
      price: "0.25",
      provider: "Social_Sniper",
      status: "unlocked",
      description: "Real-time social sentiment tracking",
      bullish: 85,
    },
    {
      id: "arbitrage",
      name: "DEX Arbitrage Finder",
      price: "1.00",
      provider: "FlashBot_Node",
      status: "locked",
      description: "Automated arbitrage opportunity detection",
      bullish: 60,
    },
  ]

  const handleUnlock = (productId: string) => {
    setSelectedProduct(productId)
    setShowPaymentModal(true)
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold mb-2">Alpha Marketplace</h2>
        <p className="text-muted-foreground">Premium trading insights via x402 protocol</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.map((product) => (
          <AlphaProductCard key={product.id} product={product} onUnlock={handleUnlock} />
        ))}
      </div>

      {showPaymentModal && (
        <X402Modal
          product={products.find((p) => p.id === selectedProduct)!}
          onClose={() => setShowPaymentModal(false)}
        />
      )}
    </div>
  )
}
