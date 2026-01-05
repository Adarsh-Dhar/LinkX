"use client"

import { useEffect, useRef } from "react"

export default function LiveTerminal() {
  const terminalRef = useRef<HTMLDivElement>(null)

  const logs = [
    "[10:42:01] Searching for alpha sources...",
    "[10:42:05] Found endpoint: /alpha/insight/VVS (402 Payment Required)",
    "[10:42:06] x402 Protocol: Generating EIP-712 Signature...",
    '[10:42:08] Payment Verified. Insight received: { sentiment: "HIGH_VOL" }',
    "[10:42:09] Cross-referencing with CoinGecko... MATCH.",
    "[10:42:11] Executing Swap on VVS Router... Success (Tx: 0x5a...f2)",
    "[10:42:13] Transaction Confirmed: +2.3% profit",
    "[10:42:15] Monitoring next opportunity...",
    "[10:42:22] Found anomaly in CRO/USDC pair",
    "[10:42:25] Initiating whale detection algorithm...",
    "[10:42:28] Whale activity detected! Volume: 450K CRO",
    '[10:42:30] Requesting "Whale Watcher" insight...',
    "[10:42:31] Processing x402 payment invoice...",
    "[10:42:33] Payment accepted. Analyzing data...",
    "[10:42:35] Executing arbitrage strategy...",
    "[10:42:38] Trade executed. Profit: +1.8%",
  ]

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [])

  return (
    <div className="p-8 h-full flex flex-col">
      <div className="mb-6">
        <h2 className="text-3xl font-bold mb-2">Live Terminal</h2>
        <p className="text-muted-foreground">Agent execution logs and data streams</p>
      </div>

      <div
        ref={terminalRef}
        className="flex-1 glass neon-border rounded-lg p-6 overflow-y-auto font-mono text-sm bg-black/80 border border-secondary/50"
      >
        <div className="space-y-1">
          {logs.map((log, idx) => (
            <div key={idx} className="terminal-text">
              {log}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
