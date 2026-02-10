"use client";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function RatingsChart({ ratings }: { ratings: { time: string, rating: number }[] }) {
  if (!ratings || ratings.length === 0) return null;
  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={ratings}>
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
