"use client";

import LogRatingForm from "./LogRatingForm";
import RatingsChart from "@/components/market/ratings-chart";
import { useState } from "react";

export default function LogRatingClient({ node, ratings }: { node: any; ratings: any[] }) {
  // Calculate aggregate rating from user feedback only
  const userFeedbackRatings = Array.isArray(node.dataLogs)
    ? node.dataLogs
        .map((log: any) => typeof log.userRating?.rating === "number" ? log.userRating.rating : null)
        .filter((r: number | null): r is number => r !== null)
    : [];
  const initialAggregate = userFeedbackRatings.length > 0
    ? userFeedbackRatings.reduce((sum: number, r: number) => sum + r, 0) / userFeedbackRatings.length
    : 0;
  const [aggregateRating, setAggregateRating] = useState(initialAggregate);

  return (
    <div className="p-6 space-y-8">
      <header>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold">{node.title}</h1>
            <p className="text-muted-foreground">{node.description}</p>
            <div className="mt-2 badge">{node.more_context}</div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium">Aggregate Rating</div>
            <div className="text-2xl font-bold text-yellow-500">{aggregateRating === 0 ? '0.00' : aggregateRating.toFixed(2)}/10</div>
          </div>
        </div>
      </header>

      {/* Ratings History Graph (only if data exists) */}
      {ratings.length > 0 && (
        <section className="bg-card p-4 rounded-lg border">
          <h2 className="text-xl font-semibold mb-4">Ratings Over Time</h2>
          <RatingsChart ratings={ratings} />
        </section>
      )}

      {/* Node Data Logs with Rating Form */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Node Data Logs</h2>
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm text-left">
            <thead className="bg-muted">
              <tr>
                <th className="p-3">Timestamp</th>
                <th className="p-3">Data Point (Signal)</th>
                <th className="p-3">User Feedback (1-10)</th>
              </tr>
            </thead>
            <tbody>
              {node.dataLogs.map((log: any) => (
                <tr key={log.id} className="border-t">
                  <td className="p-3">{new Date(log.fetchedAtFormatted).toISOString().replace('T', ' ').replace(/\..+/, '')}</td>
                  <td className="p-3 font-mono text-xs max-w-xs overflow-hidden text-ellipsis">{JSON.stringify(log.data)}</td>
                  <td className="p-3">
                    <LogRatingForm
                      logId={log.id}
                      nodeId={node.id}
                      initialRating={log.userRating?.rating}
                      initialComment={log.userRating?.comment}
                      onSaved={newAvg => setAggregateRating(newAvg)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}