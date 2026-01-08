"use client"

import { Activity, Zap, TrendingUp } from "lucide-react"
import StatCard from "./stat-card"
import AgentCard from "./agent-card"
import ActivityFeed from "./activity-feed"
import { TradingView } from "./trading-view"

export default function Dashboard() {
  return (
    <div className="p-8 space-y-8">
      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard label="Wallet Balance" value="1,420 CRO" icon={<Zap className="text-secondary" size={24} />} />
        <StatCard label="Alpha Purchased" value="12" icon={<Activity className="text-primary" size={24} />} />
        <StatCard label="Total Profit" value="+14.5%" icon={<TrendingUp className="text-accent" size={24} />} />
      </div>

      {/* Live Chart */}
      <div className="w-full">
        <TradingView />
      </div>

      {/* Active Agents & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <AgentCard />
        </div>
        <div className="lg:col-span-2">
          <ActivityFeed />
        </div>
      </div>
    </div>
  )
}
