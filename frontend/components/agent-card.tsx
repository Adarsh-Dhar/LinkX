"use client"

import { useState } from "react"
import { Play, Square } from "lucide-react"

export default function AgentCard() {
  const [isRunning, setIsRunning] = useState(true)

  return (
    <div className="glass glow-accent p-6 rounded-lg border border-border/30">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <div className={`w-3 h-3 rounded-full ${isRunning ? "bg-green-500 animate-pulse" : "bg-red-500"}`}></div>
        Active Agents
      </h3>

      <div className="space-y-4">
        <div className="bg-black/40 p-4 rounded-lg border border-secondary/30">
          <p className="text-sm font-mono text-secondary mb-3">VVS_WHALE_WATCHER_BOT</p>
          <p className="text-xs text-muted-foreground mb-4">Status: {isRunning ? "Running" : "Stopped"}</p>
          <button
            onClick={() => setIsRunning(!isRunning)}
            className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-all text-sm font-medium ${
              isRunning
                ? "bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30"
                : "bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30"
            }`}
          >
            {isRunning ? <Square size={16} /> : <Play size={16} />}
            {isRunning ? "Stop Agent" : "Start Agent"}
          </button>
        </div>
      </div>
    </div>
  )
}
