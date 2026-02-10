"use client";
import Dashboard from "@/components/dashboard";
import { TradingView } from "@/components/trading-view";
import { DataStreamWidget } from "@/components/data-stream-widget";
import { DecisionLog } from "@/components/decision-log";
import { ROICalculator } from "@/components/roi-calculator";

export default function DashboardPage() {
  return (
    <>
      <Dashboard />
      <div className="mt-8 w-full grid grid-cols-4 gap-4">
        <TradingView />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        <div className="bg-zinc-900 border border-zinc-700 rounded-lg shadow p-6 text-zinc-100 [&>*]:bg-transparent">
          <DataStreamWidget />
        </div>
        <div className="bg-zinc-900 border border-zinc-700 rounded-lg shadow p-6 text-zinc-100 [&>*]:bg-transparent">
          <DecisionLog />
        </div>
        <div className="bg-zinc-900 border border-zinc-700 rounded-lg shadow p-6 text-zinc-100 [&>*]:bg-transparent">
          <ROICalculator />
        </div>
      </div>
    </>
  );
}
