
"use client";

import { useEffect, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ArrowUpRight, ArrowDownRight, Zap, TrendingUp, TrendingDown, Flame, Shield, Play, Square } from "lucide-react";

interface Activity {
  id: string;
  type: 'trade' | 'node_purchase' | 'price_movement';
  title: string;
  description: string;
  value: number;
  isPositive: boolean;
  timestamp: Date;
  icon: string;
}

export function ActivityFeed() {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchActivity() {
      try {
        const res = await fetch("/api/activity/recent");
        if (res.ok) {
          const data = await res.json();
          setActivities(data.activities.map((a: any) => ({
            ...a,
            timestamp: new Date(a.timestamp),
          })));
        }
      } catch (error) {
        console.error("Failed to fetch activity", error);
      } finally {
        setLoading(false);
      }
    }

    fetchActivity();
    const interval = setInterval(fetchActivity, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  const getIcon = (activity: Activity) => {
    switch (activity.icon) {
      case 'trade':
        return activity.isPositive ? (
          <ArrowUpRight className="h-5 w-5 text-green-500" />
        ) : (
          <ArrowDownRight className="h-5 w-5 text-red-500" />
        );
      case 'node':
        return <Zap className="h-5 w-5 text-blue-500" />;
      case 'score':
        return <Flame className="h-5 w-5 text-orange-500" />;
      case 'signal':
        return <TrendingUp className="h-5 w-5 text-purple-500" />;
      case 'shield':
        return <Shield className="h-5 w-5 text-yellow-500" />;
      case 'play':
        return <Play className="h-5 w-5 text-gray-400" />;
      case 'stop':
        return <Square className="h-5 w-5 text-gray-400" />;
      case 'trend-up':
        return <TrendingUp className="h-5 w-5 text-green-500" />;
      case 'trend-down':
        return <TrendingDown className="h-5 w-5 text-red-500" />;
      default:
        return <Zap className="h-5 w-5 text-zinc-500" />;
    }
  };

  if (loading) {
    return <div className="text-sm text-muted-foreground">Loading activity...</div>;
  }

  if (activities.length === 0) {
    return <div className="text-sm text-muted-foreground">No recent activity.</div>;
  }

  return (
    <div className="space-y-4">
      {activities.map((activity) => (
        <div key={activity.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-zinc-900/50 transition">
          <div className="flex-shrink-0">
            {getIcon(activity)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-zinc-100 truncate">
              {activity.title}
            </p>
            <p className="text-xs text-zinc-400 truncate">
              {activity.description}
            </p>
          </div>
          <div className="flex-shrink-0 text-right">
            <p className={`text-sm font-medium ${activity.isPositive ? "text-green-500" : "text-red-500"}`}>
              {activity.isPositive ? "+" : ""}{(activity.value ?? 0).toFixed(2)}
            </p>
            <p className="text-xs text-zinc-500">
              {activity.timestamp.toLocaleTimeString()}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
