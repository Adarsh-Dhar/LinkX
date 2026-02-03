import { useEffect, useState } from "react";

export function DataStreamWidget() {
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      try {
        const res = await fetch("/api/agent/data-log");
        if (!res.ok) return;
        const json = await res.json();
        if (isMounted) setData(json.dataLog || []);
      } catch {}
    };
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="p-4 border rounded bg-white shadow">
      <h3 className="font-bold mb-2">Data Stream</h3>
      <div className="h-40 overflow-y-auto text-xs">
        {data.length === 0 ? (
          <div className="text-gray-400">No data yet.</div>
        ) : (
          data.map((entry, i) => (
            <div key={i} className="mb-1">
              <span className="text-blue-600">[{entry.fetchedAt}]</span> <b>{entry.nodeName}</b>: {entry.normalized ?? entry.data}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
