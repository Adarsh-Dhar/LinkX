import { Key } from "react";

export default function DecisionLog({ log } : { log: any[] }) {
  const safeLog = Array.isArray(log) ? log : [];
  return (
    <div>
      <h3 className="font-bold mb-2">Decision Log</h3>
      <div className="h-40 overflow-y-auto text-xs">
        {safeLog.length === 0 ? (
          <div className="text-gray-400">No decisions yet.</div>
        ) : (
          safeLog.map((entry: { context: string; decidedAt: string | number | Date; }, i: Key | null | undefined) => {
            let details = { action: "N/A", amount: "N/A" };
            try {
              if (entry.context && typeof entry.context === 'string' && entry.context.startsWith('{')) {
                const parsed = JSON.parse(entry.context);
                details = { ...details, ...parsed };
              }
            } catch (e) {}
            return (
              <div key={i} className="mb-1 flex gap-2">
                <span className="font-bold uppercase">{details.action}</span>
                <span>{details.amount}</span>
                <span className="text-muted-foreground text-xs">
                  {entry.decidedAt ? new Date(entry.decidedAt).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                  }) : ''}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
