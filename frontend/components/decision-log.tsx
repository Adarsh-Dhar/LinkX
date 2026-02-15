"use client";

import { useEffect, useState } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function DecisionLog() {
  const [decisions, setDecisions] = useState<any[]>([]);

  useEffect(() => {
    const fetchDecisions = async () => {
      try {
        const res = await fetch("/api/agent/decision-log");
        const data = await res.json();
        // The API returns { decisionLog: [...] }
        setDecisions(Array.isArray(data.decisionLog) ? data.decisionLog : []);
      } catch (e) {
        console.error("Failed to fetch decisions", e);
        setDecisions([]);
      }
    };
    fetchDecisions();
    const interval = setInterval(fetchDecisions, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Action</TableHead>
            <TableHead>Amount</TableHead>
            <TableHead className="text-right">Date and Time</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {decisions.length === 0 ? (
            <TableRow key="no-data"><TableCell colSpan={3} className="text-center">No decisions yet.</TableCell></TableRow>
          ) : (
            decisions.map((d) => {
              let details = { action: "ANALYSIS", amount: "N/A" };
              try {
                // Parse the JSON object created by the Python agent
                if (d.context?.startsWith("{")) {
                    const parsed = JSON.parse(d.context);
                    details.action = parsed.action || "ANALYSIS";
                    details.amount = parsed.amount || "N/A";
                } else {
                    details.amount = d.context;
                }
              } catch (e) {}
              return (
                <TableRow key={d.id}>
                  <TableCell className="font-bold uppercase text-primary">{details.action}</TableCell>
                  <TableCell>{details.amount}</TableCell>
                  <TableCell className="text-right text-muted-foreground text-xs">
                    {new Date(d.decidedAt).toLocaleString()}
                  </TableCell>
                </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>
    </div>
  );
}