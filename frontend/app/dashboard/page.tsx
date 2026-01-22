"use client";
import Dashboard from "@/components/dashboard";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useEffect, useState } from "react";

export default function DashboardPage() {
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    fetch("http://localhost:3600/api/dashboard/chart")
      .then((res) => res.json())
      .then((data) => setChartData(data));
  }, []);

  return (
    <>
      <Dashboard />
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Standalone Cumulative Returns Graph</CardTitle>
        </CardHeader>
        <CardContent className="pl-2">
          <div className="h-[350px]">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorReturns" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22c55e" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#22c55e" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `$${value}`} />
                  <Tooltip contentStyle={{ backgroundColor: "#111", border: "1px solid #333" }} />
                  <Area type="monotone" dataKey="value" stroke="#22c55e" fill="url(#colorReturns)" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-muted-foreground">
                No trading data yet
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </>
  );
}
