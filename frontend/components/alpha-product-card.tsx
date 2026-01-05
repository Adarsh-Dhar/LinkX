"use client"

import { Lock, Unlock } from "lucide-react"

interface Product {
  id: string
  name: string
  price: string
  provider: string
  status: "locked" | "unlocked"
  description: string
  bullish: number
}

interface AlphaProductCardProps {
  product: Product
  onUnlock: (productId: string) => void
}

export default function AlphaProductCard({ product, onUnlock }: AlphaProductCardProps) {
  const isLocked = product.status === "locked"

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
        <button
          onClick={() => onUnlock(product.id)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            isLocked
              ? "bg-gradient-to-r from-primary to-accent hover:shadow-lg hover:shadow-primary/30 text-white"
              : "bg-green-500/20 text-green-400 border border-green-500/30"
          }`}
        >
          {isLocked ? "Purchase" : "Active"}
        </button>
      </div>
    </div>
  )
}
