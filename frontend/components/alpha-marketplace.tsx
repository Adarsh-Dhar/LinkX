"use client"

import { useState, useEffect } from "react"
import AlphaProductCard from "./alpha-product-card"
import X402Modal from "./x402-modal"

interface Signal {
  ticker: string
  signal: string
  confidence: number
  sentiment: string
  recommended_action: string
  amount_usdc?: number
  reason?: string
}

export default function AlphaMarketplace() {
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null)
  const [showPaymentModal, setShowPaymentModal] = useState(false)
  const [signals, setSignals] = useState<Signal[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Fetch live signals from server
  useEffect(() => {
    const fetchSignals = async () => {
      try {
        const response = await fetch("http://localhost:3050/signals")
        if (response.ok) {
          const data = await response.json()
          setSignals(data.signals || [])
        }
      } catch (error) {
        console.error("Failed to fetch signals:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchSignals()
    
    // Refresh signals every 30 seconds
    const interval = setInterval(fetchSignals, 30000)
    return () => clearInterval(interval)
  }, [])

  // Convert signals to product format
  const products = signals.map((signal) => ({
    id: signal.ticker.toLowerCase(),
    ticker: signal.ticker,
    name: `${signal.ticker} ${signal.recommended_action} Signal`,
    price: "0.10",
    provider: "Alpha-Consumer AI",
    status: "locked" as const,
    description: signal.reason || `${signal.sentiment} sentiment detected with ${(signal.confidence * 100).toFixed(0)}% confidence`,
    bullish: Math.round(signal.confidence * 100),
  }))

  // Add some default products if no signals available
  const defaultProducts = [
    {
      id: "whale-watcher",
      name: "VVS Whale Watcher",
      price: "0.10",
      provider: "HedgeFund_AI",
      status: "locked" as const,
      description: "Monitor large whale movements on VVS",
      bullish: 75,
    },
    {
      id: "sentiment",
      name: "CRO Sentiment Analysis",
      price: "0.25",
      provider: "Social_Sniper",
      status: "locked" as const,
      description: "Real-time social sentiment tracking",
      bullish: 85,
    },
    {
      id: "arbitrage",
      name: "DEX Arbitrage Finder",
      price: "1.00",
      provider: "FlashBot_Node",
      status: "locked" as const,
      description: "Automated arbitrage opportunity detection",
      bullish: 60,
    },
  ]

  const displayProducts = products.length > 0 ? products : defaultProducts

  const handleUnlock = (productId: string) => {
    setSelectedProduct(productId)
    setShowPaymentModal(true)
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold mb-2">Alpha Marketplace</h2>
          <p className="text-muted-foreground">Premium trading insights via x402 protocol</p>
        </div>
        {!isLoading && signals.length > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-muted-foreground">Live Signals</span>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          <p className="text-muted-foreground mt-4">Loading trading signals...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayProducts.map((product) => (
            <AlphaProductCard key={product.id} product={product} onUnlock={handleUnlock} />
          ))}
        </div>
      )}

      {showPaymentModal && (
        <X402Modal
          product={displayProducts.find((p) => p.id === selectedProduct)!}
          onClose={() => setShowPaymentModal(false)}
        />
      )}
    </div>
  )
}
