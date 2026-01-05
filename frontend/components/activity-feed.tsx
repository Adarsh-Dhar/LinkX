export default function ActivityFeed() {
  const activities = [
    { icon: "💰", action: "Bought 'Whale Watcher' Insight", time: "5 min ago" },
    { icon: "🔄", action: "Swapped 10 USDC → VVS", time: "12 min ago" },
    { icon: "📊", action: "Received 'Sentiment Analysis' Update", time: "18 min ago" },
    { icon: "✓", action: "x402 Payment Verified", time: "25 min ago" },
    { icon: "🚀", action: "Strategy Execution Completed", time: "32 min ago" },
  ]

  return (
    <div className="glass glow-secondary p-6 rounded-lg border border-border/30">
      <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>

      <div className="space-y-3">
        {activities.map((activity, idx) => (
          <div key={idx} className="flex items-center justify-between py-3 border-b border-border/20 last:border-0">
            <div className="flex items-center gap-3">
              <span className="text-xl">{activity.icon}</span>
              <p className="text-sm text-foreground">{activity.action}</p>
            </div>
            <span className="text-xs text-muted-foreground">{activity.time}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
