"use client"

import { Zap, Wifi, Wallet } from "lucide-react"
import { useWallet } from "@/hooks/use-wallet"

export default function TopBar() {
  const { isConnected, isConnecting, shortAddress, balance, usdcBalance, connect, disconnect } =
    useWallet()

  return (
    <div className="h-16 glass border-b border-border/30 px-6 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500 glow-secondary animate-pulse"></div>
          <span className="text-sm text-muted-foreground">
            Agent Status: <span className="text-foreground font-semibold">ONLINE</span>
          </span>
        </div>

        <div className="flex items-center gap-2 text-muted-foreground">
          <Wifi size={16} className="text-secondary" />
          <span className="text-sm">
            Network: <span className="text-foreground font-semibold">Cronos</span>
          </span>
        </div>
      </div>

      {isConnected ? (
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-xs text-muted-foreground">Balance</div>
            <div className="text-sm font-semibold">
              {parseFloat(balance || "0").toFixed(2)} CRO • {parseFloat(usdcBalance || "0").toFixed(2)} USDC
            </div>
          </div>
          <button
            onClick={disconnect}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-primary to-accent hover:shadow-lg hover:shadow-primary/30 transition-all text-white font-medium text-sm"
          >
            <Wallet size={16} />
            {shortAddress}
          </button>
        </div>
      ) : (
        <button
          onClick={connect}
          disabled={isConnecting}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-primary to-accent hover:shadow-lg hover:shadow-primary/30 disabled:opacity-50 transition-all text-white font-medium text-sm"
        >
          <Zap size={16} />
          {isConnecting ? "Connecting..." : "Connect Wallet"}
        </button>
      )}
    </div>
  )
}
