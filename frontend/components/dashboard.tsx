"use client";

import { useEffect, useState } from "react";
import { usePortfolioSync } from "@/hooks/use-portfolio-sync";

// Type for chart data points
interface ChartPoint {
  time: string;
  timestamp?: string;
  value?: number;
  wxtzBalance?: number;
  usdcBalance?: number;
}
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Activity, ArrowUpRight, DollarSign, Wallet, Brain, BarChart3 } from "lucide-react";
import StatCard from "./stat-card";
import { ActivityFeed } from "./activity-feed";
import { Button } from "@/components/ui/button";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

// Default empty state to prevent UI flickering before load
const defaultStats = {
  wxtzBalance: 0,
  usdcBalance: 0,
  walletBalanceUsd: 0,
  alphaPurchased: 0,
  totalPnL: 0,
  profitPercent: 0,
  winRate: 0,
  totalTrades: 0,
  avgConfidence: 0,
};

export default function Dashboard() {
  const { syncPortfolio } = usePortfolioSync();
  const [stats, setStats] = useState(defaultStats);
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  // Derived chart data with 'value' key for Recharts
  const chartDataWithValue: ChartPoint[] = chartData.map((d) => ({ ...d, value: d.value || 0 }));
  const [loading, setLoading] = useState(true);

  // FETCH DATA
  useEffect(() => {
    async function fetchDashboardData() {
      try {
        // Sync portfolio to save latest balances
        await syncPortfolio();
        // Fetch dashboard stats and chart data
        const [statsRes, chartRes] = await Promise.all([
          fetch("/api/dashboard/stats"),
          fetch("/api/dashboard/chart"),
        ]);
        if (statsRes.ok) {
          const statsData = await statsRes.json();
          setStats(statsData);
        }
        if (chartRes.ok) {
          const chartData = await chartRes.json();
          setChartData(chartData);
        }
      } catch (error) {
        console.error("Failed to load dashboard data:", error);
      } finally {
        setLoading(false);
      }
    }
    // Initial Fetch
    fetchDashboardData();
    // Poll every 1 minute for live updates
    const interval = setInterval(fetchDashboardData, 60000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex-1 space-y-4 p-4 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <div className="flex items-center space-x-2">
          <Button>Download Report</Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* STATS GRID */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Wallet Balance"
              value={`${stats.wxtzBalance.toFixed(4)} WXTZ • ${stats.usdcBalance.toFixed(2)} USDC`}
              icon={<Wallet />}
            />
            <StatCard
              label="Win Rate"
              value={`${stats.winRate.toFixed(1)}%`}
              icon={<BarChart3 />}
            />
            <StatCard
              label="Total Profit"
              value={`$${stats.totalPnL.toFixed(2)}`}
              icon={<DollarSign />}
            />
            <StatCard
              label="Alpha Purchased"
              value={stats.alphaPurchased.toString()}
              icon={<Activity />}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7 w-full">
            {/* CHART CARD */}
            <Card className="col-span-4 w-full min-w-0">
              <CardHeader>
                <CardTitle>Cumulative Returns</CardTitle>
              </CardHeader>
              <CardContent className="pl-2 w-full">
                <div className="h-[350px] w-full min-h-[350px]">
                  {chartDataWithValue.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={350} style={{ display: 'flex' }}>
                      <LineChart data={chartDataWithValue}>
                        <XAxis
                          dataKey="time"
                          stroke="#888888"
                          fontSize={12}
                          tickLine={false}
                          axisLine={false}
                        />
                        <YAxis
                          stroke="#888888"
                          fontSize={12}
                          tickLine={false}
                          axisLine={false}
                          tickFormatter={(value) => `$${value}`}
                        />
                        <Tooltip 
                          contentStyle={{ backgroundColor: "#111", border: "1px solid #333" }}
                        />
                        <Line
                          type="monotone"
                          dataKey="value"
                          stroke="#adfa1d"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex h-full items-center justify-center text-muted-foreground">
                      No trading data yet
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* ACTIVITY FEED CARD */}
            <Card className="col-span-3">
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <ActivityFeed />
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
