"use client";
import Dashboard from "@/components/dashboard";
import { DataStreamWidget } from "@/components/data-stream-widget";
import { DecisionLog } from "@/components/decision-log";
import { ROICalculator } from "@/components/roi-calculator";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useEffect, useState, useRef } from "react";


export default function DashboardPage() {
  const [chartData, setChartData] = useState<{ time: string; value: number }[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    let isMounted = true;
    
    const fetchPrices = async () => {
      try {
        const chartRes = await fetch("/api/dashboard/chart");
        if (chartRes.ok) {
          const prices = await chartRes.json();
          if (Array.isArray(prices) && prices.length > 0 && isMounted) {
            // On first load, populate chart with all historical data
            if (!isInitialized) {
              const formattedData = prices
                .map((p: any) => ({
                  time: p.time,
                  value: parseFloat(p.close) || 0.06
                }))
                .filter((d: any) => !isNaN(d.value) && typeof d.value === 'number');
              
              setChartData(formattedData);
              setIsInitialized(true);
            } else {
              // On subsequent fetches, add one new point
              const now = new Date();
              const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
              const latestPrice = prices[prices.length - 1];
              const value = parseFloat(latestPrice.close) || 0.06;
              
              setChartData(prev => {
                const newData = [...prev, { time: timeStr, value }];
                if (newData.length > 60) newData.shift();
                return newData;
              });
            }
          }
        }
      } catch (e) {
        console.error("Failed to fetch price data:", e);
      }
    };
    
    // Initial fetch immediately
    fetchPrices();
    
    // Poll every 1 minute
    pollingRef.current = setInterval(fetchPrices, 60000);
    
    return () => {
      isMounted = false;
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [isInitialized]);

  return (
    <>
      <Dashboard />
      <Card className="mt-8 w-full">
        <CardHeader>
          <CardTitle>CRO/USDC Price Graph</CardTitle>
        </CardHeader>
        <CardContent className="pl-2 w-full">
          <div className="h-[350px] w-full">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorCROUSDC" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => typeof value === 'number' && !isNaN(value) ? value.toFixed(4) : '0.0000'} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#111", border: "1px solid #333" }}
                    formatter={(value: any) => {
                      if (typeof value === 'number' && !isNaN(value)) {
                        return value.toFixed(6);
                      }
                      return '0.000000';
                    }}
                  />
                  <Area type="monotone" dataKey="value" stroke="#0ea5e9" fill="url(#colorCROUSDC)" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-muted-foreground">
                No CRO/USDC price data yet
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        <DataStreamWidget />
        <DecisionLog />
        <ROICalculator />
      </div>
    </>
  );
}
