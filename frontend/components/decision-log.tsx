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
              <span className="text-green-600">[{entry.decidedAt}]</span> <b>{entry.action}</b> on <b>{entry.token}</b> (Signal: {entry.signal}, Reason: {entry.reason})
            </div>
          ))
        )}
      </div>
    </div>
  );
}
