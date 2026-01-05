"use client"

import { useState } from "react"
import { ArrowRightLeft, Zap } from "lucide-react"

export default function TradingView() {
  const [fromAmount, setFromAmount] = useState("10")
  const [toAmount, setToAmount] = useState("150")

  return (
    <div className="p-8 flex flex-col items-center justify-start">
      <div className="mb-8">
        <h2 className="text-3xl font-bold mb-2">Trading View</h2>
        <p className="text-muted-foreground">Auto-execute trading strategies</p>
      </div>

      <div className="w-full max-w-md space-y-6">
        {/* Swap Interface */}
        <div className="glass glow-primary p-8 rounded-lg border border-border/30">
          {/* From */}
          <div className="mb-4">
            <label className="text-xs text-muted-foreground block mb-2">From</label>
            <div className="glass border border-border/30 rounded-lg p-4 flex items-center justify-between">
              <input
                type="number"
                value={fromAmount}
                onChange={(e) => setFromAmount(e.target.value)}
                className="bg-transparent text-2xl font-bold text-foreground outline-none w-full"
              />
              <span className="text-lg font-bold text-foreground ml-2">USDC</span>
            </div>
          </div>

          {/* Swap Button */}
          <div className="flex justify-center mb-4">
            <button className="p-3 bg-gradient-to-r from-primary to-accent rounded-full hover:shadow-lg hover:shadow-primary/30 transition-all">
              <ArrowRightLeft size={20} className="text-white" />
            </button>
          </div>

          {/* To */}
          <div className="mb-6">
            <label className="text-xs text-muted-foreground block mb-2">To</label>
            <div className="glass border border-border/30 rounded-lg p-4 flex items-center justify-between">
              <input
                type="number"
                value={toAmount}
                onChange={(e) => setToAmount(e.target.value)}
                className="bg-transparent text-2xl font-bold text-foreground outline-none w-full"
              />
              <span className="text-lg font-bold text-secondary ml-2">VVS</span>
            </div>
          </div>

          {/* Execution Button */}
          <button className="w-full flex items-center justify-center gap-2 px-6 py-4 rounded-lg bg-gradient-to-r from-primary via-accent to-secondary hover:shadow-2xl hover:shadow-primary/40 transition-all text-white font-bold text-lg">
            <Zap size={24} />
            Auto-Execute Strategy
          </button>
        </div>

        {/* Chart Placeholder */}
        <div className="glass glow-accent p-6 rounded-lg border border-border/30">
          <h3 className="text-sm font-semibold text-foreground mb-4">VVS Price Action</h3>
          <div className="w-full h-64 bg-black/40 rounded-lg border border-secondary/30 flex items-center justify-center">
            <div className="text-center">
              <p className="text-muted-foreground text-sm">📊 Chart visualization</p>
              <p className="text-muted-foreground text-xs mt-2">Current: $0.0234</p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4">
          <div className="glass p-4 rounded-lg border border-border/30">
            <p className="text-xs text-muted-foreground mb-2">24H Change</p>
            <p className="text-xl font-bold text-secondary">+8.5%</p>
          </div>
          <div className="glass p-4 rounded-lg border border-border/30">
            <p className="text-xs text-muted-foreground mb-2">Volume</p>
            <p className="text-xl font-bold text-primary">2.3M</p>
          </div>
        </div>
      </div>
    </div>
  )
}
