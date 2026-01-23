import { useEffect, useState } from "react";

export function ROICalculator() {
  const [roi, setRoi] = useState<{ cost: number; profit: number } | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchRoi = async () => {
      try {
        const res = await fetch("/api/agent/roi");
        if (!res.ok) return;
        const json = await res.json();
        if (isMounted) setRoi(json.roi || null);
      } catch {}
    };
    fetchRoi();
    const interval = setInterval(fetchRoi, 10000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="p-4 border rounded bg-white shadow mt-4">
      <h3 className="font-bold mb-2">ROI Calculator</h3>
      {roi ? (
        <div>
          <div>Data Cost: <b>{roi.cost.toFixed(2)} USDC</b></div>
          <div>Profit from Trades: <b>{roi.profit.toFixed(2)} USDC</b></div>
          <div className="mt-2">ROI: <b>{((roi.profit - roi.cost) / (roi.cost || 1) * 100).toFixed(1)}%</b></div>
        </div>
      ) : (
        <div className="text-gray-400">No ROI data yet.</div>
      )}
    </div>
  );
}
