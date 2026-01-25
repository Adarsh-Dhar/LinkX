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
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchPrices = async () => {
      try {
        const [croRes, usdcRes] = await Promise.all([
          fetch("http://localhost:3050/market/price/CRO"),
          fetch("http://localhost:3050/market/price/USDC")
        ]);
        const croData = await croRes.json();
        const usdcData = await usdcRes.json();
        if (!croData.price || !usdcData.price) return;
        const now = new Date();
        const timeStr = `${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}`;
        const ratio = croData.price / usdcData.price;
        if (isMounted) {
          setChartData(prev => {
            const newData = [...prev, { time: timeStr, value: ratio }];
            if (newData.length > 30) newData.shift();
            return newData;
          });
        }
      } catch (e) {
        // Optionally handle error
      }
    };
    fetchPrices();
    pollingRef.current = setInterval(fetchPrices, 10000); // Poll every 10s
    return () => {
      isMounted = false;
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

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
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => value.toFixed(4)} />
                  <Tooltip contentStyle={{ backgroundColor: "#111", border: "1px solid #333" }} />
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
