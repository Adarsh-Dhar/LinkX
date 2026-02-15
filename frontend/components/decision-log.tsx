import { useEffect, useState } from "react";

export function DecisionLog() {
  const [log, setLog] = useState<any[]>([]);

  useEffect(() => {
    let isMounted = true;
    const fetchLog = async () => {
      try {
        const res = await fetch("/api/agent/decision-log");
        if (!res.ok) return;
        const json = await res.json();
        if (isMounted) setLog(json.decisionLog || []);
      } catch {}
    };
    fetchLog();
    const interval = setInterval(fetchLog, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="p-4 border rounded bg-white shadow mt-4">
      <h3 className="font-bold mb-2">Decision Log</h3>
      <div className="h-40 overflow-y-auto text-xs">
        {log.length === 0 ? (
          <div className="text-gray-400">No decisions yet.</div>
        ) : (
          log.map((entry, i) => (
            <div key={i} className="mb-1">
              <span className="text-muted-foreground text-xs">
                {entry.decidedAt ? new Date(entry.decidedAt).toLocaleString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit'
                }) : ''}
              </span>
              {(() => {
                let details = { action: "N/A", ticker: "N/A", signal: "N/A", reason: entry.context };
                try {
                  if (entry.context && typeof entry.context === 'string' && entry.context.startsWith('{')) {
                    const parsed = JSON.parse(entry.context);
                    details = { ...details, ...parsed };
                  }
                } catch (e) {}
                return (
                  <>
                    <b>{details.action}</b> on <b>{details.ticker}</b> (Signal: {details.signal !== "N/A" ? `${(Number(details.signal) * 100).toFixed(0)}%` : "N/A"}, Reason: {details.reason})
                  </>
                );
              })()}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
