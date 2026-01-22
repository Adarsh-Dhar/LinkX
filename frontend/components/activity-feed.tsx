
"use client";

import { useEffect, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface Trade {
  id: string;
  pair: string;
  amount: string;
  pnl: number;
  status: string;
  timestamp: string;
}

export function ActivityFeed() {
  const [trades, setTrades] = useState<Trade[]>([]);

  useEffect(() => {
    async function fetchTrades() {
      try {
        const res = await fetch("/api/trades/history");
        if (res.ok) {
          const data = await res.json();
          setTrades(data);
        }
      } catch (error) {
        console.error("Failed to fetch trade history", error);
      }
    }

    fetchTrades();
    const interval = setInterval(fetchTrades, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  if (trades.length === 0) {
    return <div className="text-sm text-muted-foreground">No recent activity.</div>;
  }

  return (
    <div className="space-y-8">
      {trades.map((trade) => (
        <div key={trade.id} className="flex items-center">
          <Avatar className="h-9 w-9">
            <AvatarImage src="/avatars/01.png" alt="Avatar" />
            <AvatarFallback>{trade.pair.substring(0, 2)}</AvatarFallback>
          </Avatar>
          <div className="ml-4 space-y-1">
            <p className="text-sm font-medium leading-none">
              Swap {trade.pair}
            </p>
            <p className="text-xs text-muted-foreground">
              {new Date(trade.timestamp).toLocaleTimeString()}
            </p>
          </div>
          <div className={`ml-auto font-medium ${trade.pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
            {trade.pnl >= 0 ? "+" : ""}${trade.pnl.toFixed(2)}
          </div>
        </div>
      ))}
    </div>
  );
}
