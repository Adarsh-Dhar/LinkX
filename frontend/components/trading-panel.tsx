"use client"

import { useState } from "react"
import { Send, Play, AlertCircle, CheckCircle, Loader } from "lucide-react"

interface TradeRequest {
  token_in: string
  token_out: string
  amount: number
  simulate_only: boolean
}

interface SimulationResult {
  success: boolean
  simulation: {
    simulation_id: string
    timestamp: string
    token_in: string
    token_out: string
    amount_in: number
    predicted_amount_out: number
    confidence: number
    neural_decision: string
    reasoning: string
  }
  nodes_used_count?: number
}

export default function TradingPanel() {
  const [tokenIn, setTokenIn] = useState("CRO")
  const [tokenOut, setTokenOut] = useState("USDC")
  const [amount, setAmount] = useState(100)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [recentTrades, setRecentTrades] = useState<any[]>([])

  // Allow overriding the agent API host; default to the Next.js rewrite at /api
  const API_BASE = process.env.NEXT_PUBLIC_AGENT_API ?? "/api"

  const handleRealTrade = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/trade/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token_in: tokenIn,
          token_out: tokenOut,
          amount: parseFloat(amount.toString()),
          simulate_only: false,
          slippage_tolerance: 1.0,
        }),
      })

      let data = null
      try {
        data = await response.json()
      } catch (jsonErr) {
        console.error("Failed to parse JSON response:", jsonErr)
        setError("Invalid response from server")
        return
      }

      if (response.ok) {
        setResult(data)
        setError(null)
        await fetchRecentTrades()
      } else {
        let errMsg = "Execution failed"
        if (data && typeof data === "object") {
          if (data.detail) errMsg = data.detail
          else if (data.error) errMsg = data.error
          else if (Object.keys(data).length > 0) errMsg = JSON.stringify(data)
          else errMsg = "Execution failed: No details provided"
        }
        if (data && typeof data === "object" && Object.keys(data).length === 0) {
          console.error("Trade execution failed: No details provided by backend.")
        } else {
          console.error("Trade execution failed:", data)
        }
        setError(errMsg)
      }
    } catch (err) {
      console.error("Error:", err)
      setError("Failed to execute trade")
    } finally {
      setLoading(false)
    }
  }

  const handleExecute = async () => {
    if (!result) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/trade/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token_in: tokenIn,
          token_out: tokenOut,
          amount: parseFloat(amount.toString()),
          simulate_only: false,
          slippage_tolerance: 1.0,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setResult(null)
        setError(null)
        await fetchRecentTrades()
      } else {
        setError(data.detail || "Execution failed")
      }
    } catch (err) {
      console.error("Error:", err)
      setError("Failed to execute trade")
    } finally {
      setLoading(false)
    }
  }

  const fetchRecentTrades = async () => {
    try {
      const response = await fetch(`${API_BASE}/simulations/recent?limit=5`)
      if (response.ok) {
        const trades = await response.json()
        setRecentTrades(trades)
      }
    } catch (err) {
      console.error("Error fetching recent trades:", err)
    }
  }

  return (
    <div className="w-96 bg-black/60 border-l border-cyan-500/30 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-black/80 border-b border-cyan-500/30 p-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Send className="w-5 h-5 text-cyan-400" />
          Trade Executor
        </h2>
      </div>

      {/* Trade Form - Only Real Trade */}
      <form onSubmit={handleRealTrade} className="p-4 space-y-4 flex-1 overflow-y-auto">
        <div>
          <label className="block text-sm text-gray-400 mb-2">From Token</label>
          <select
            value={tokenIn}
            onChange={(e) => setTokenIn(e.target.value)}
            className="w-full bg-black/40 border border-cyan-500/30 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
          >
            <option>CRO</option>
            <option>USDC</option>
            <option>VVS</option>
            <option>WCRO</option>
          </select>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-2">To Token</label>
          <select
            value={tokenOut}
            onChange={(e) => setTokenOut(e.target.value)}
            className="w-full bg-black/40 border border-cyan-500/30 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
          >
            <option>USDC</option>
            <option>CRO</option>
            <option>VVS</option>
            <option>WCRO</option>
          </select>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-2">Amount</label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(parseFloat(e.target.value))}
            className="w-full bg-black/40 border border-cyan-500/30 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
            placeholder="Enter amount"
            min="0"
            step="0.01"
          />
        </div>

        {/* Only Real Trade Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 text-white font-bold py-2 rounded flex items-center justify-center gap-2 transition-all"
        >
          {loading ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              Executing...
            </>
          ) : (
            <>
              <CheckCircle className="w-4 h-4" />
              Execute Real Trade
            </>
          )}
        </button>
      </form>

      {/* Results */}
      <div className="border-t border-cyan-500/30 flex flex-col flex-1 overflow-y-auto">
        {error && (
          <div className="p-4 bg-red-500/10 border-b border-red-500/30 text-red-400 text-sm flex gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <div>{error}</div>
          </div>
        )}

        {result && (
          <div className="p-4 space-y-3 bg-black/40 border-b border-green-500/30">
            <div className="bg-black/60 rounded p-3">
              <p className="text-xs text-gray-400 mb-1">Neural Decision</p>
              <p className={`text-lg font-bold ${
                result.simulation.neural_decision === "BUY"
                  ? "text-green-400"
                  : result.simulation.neural_decision === "SELL"
                  ? "text-red-400"
                  : "text-yellow-400"
              }`}>
                {result.simulation.neural_decision}
              </p>
            </div>

            <div className="bg-black/60 rounded p-3">
              <p className="text-xs text-gray-400 mb-1">Confidence Score</p>
              <p className="text-lg font-bold text-cyan-400">{(result.simulation.confidence * 100).toFixed(1)}%</p>
              <div className="h-2 bg-black/40 rounded mt-2 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 to-blue-500"
                  style={{ width: `${result.simulation.confidence * 100}%` }}
                />
              </div>
            </div>

            <div className="bg-black/60 rounded p-3">
              <p className="text-xs text-gray-400 mb-1">Predicted Output</p>
              <p className="text-base font-bold text-white">{result.simulation.predicted_amount_out.toFixed(6)} {tokenOut}</p>
            </div>

            <div className="bg-black/60 rounded p-3">
              <p className="text-xs text-gray-400 mb-1">Data Sources</p>
              <p className="text-sm text-cyan-400">{result.nodes_used_count || 0} nodes analyzed</p>
            </div>

            <div className="bg-black/60 rounded p-3">
              <p className="text-xs text-gray-400 mb-1">Reasoning</p>
              <p className="text-xs text-gray-300 line-clamp-3">{result.simulation.reasoning}</p>
            </div>
          </div>
        )}

        {/* Recent Trades */}
        {recentTrades.length > 0 && (
          <div className="p-4 space-y-2">
            <p className="text-xs font-bold text-gray-400 uppercase">Recent Trades</p>
            {recentTrades.map((trade, idx) => (
              <div key={idx} className="bg-black/40 rounded p-2 border border-cyan-500/10">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-xs text-cyan-400 font-mono">{trade.simulation_id}</span>
                  <span className={`text-xs font-bold ${trade.status === "completed" ? "text-green-400" : "text-yellow-400"}`}>
                    {trade.status}
                  </span>
                </div>
                <p className="text-xs text-gray-400">
                  {trade.token_in} → {trade.token_out} ({trade.amount_in})
                </p>
                <p className={`text-xs font-bold mt-1 ${trade.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                  P&L: ${(trade.pnl || 0).toFixed(4)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
