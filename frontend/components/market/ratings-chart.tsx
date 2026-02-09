"use client";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function RatingsChart({ nodeId }: { nodeId: string }) {
  // In a real app, you'd use SWR or useEffect to fetch historical ratings
  const mockData = [
    { time: '10:00', rating: 82 },
    { time: '11:00', rating: 85 },
    { time: '12:00', rating: 84 },
    { time: '13:00', rating: 89 },
  ];

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={mockData}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="time" />
          <YAxis domain={[0, 100]} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1f2937', border: 'none' }}
            itemStyle={{ color: '#10b981' }}
          />
          <Line 
            type="monotone" 
            dataKey="rating" 
            stroke="#10b981" 
            strokeWidth={2} 
            dot={{ r: 4 }} 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
