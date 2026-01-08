"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { Badge } from "@/components/ui/badge"

export function TradingView() {
  const [ticker, setTicker] = useState("CRO")
  const [currentPrice, setCurrentPrice] = useState(0)
  const [chartData, setChartData] = useState<any[]>([])
  const [predictionData, setPredictionData] = useState<any[]>([])
  const [isLive, setIsLive] = useState(true)

  // 1. LIVE DATA POLLING
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`http://localhost:3050/market/price/${ticker}`)
        const data = await res.json()
        
        setCurrentPrice(data.price)
        
        // Add point to chart
        const now = new Date()
        const timeStr = `${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}`
        
        setChartData(prev => {
            const newData = [...prev, { time: timeStr, price: data.price, type: "history" }]
            if (newData.length > 30) newData.shift() // Keep last 30 points
            return newData
        })
      } catch (e) {
        console.error("Fetch error:", e)
      }
    }

    // Initial fetch
    fetchData()
    // Poll every 5 seconds
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [ticker])

  // 2. LISTEN FOR "ALPHA BOUGHT" EVENTS (To show prediction)
  // In a real app, use a Context or Redux. For Hackathon, we can use a simple event listener
  useEffect(() => {
    const handleAlpha = (e: any) => {
        const prediction = e.detail?.prediction || []
        // Format prediction data to match chart
        // This is a simplified visual hack for the demo
        if (prediction.length > 0) {
           // We stop live updates to show the "Simulation" clearly
           setIsLive(false)
           // Merge current data with prediction
           const lastPoint = chartData[chartData.length - 1]
           const predPoints = prediction.map((p: any, i: number) => ({
               time: `Future +${i}m`,
               price: p.price,
               type: "prediction"
           }))
           setChartData([...chartData, ...predPoints])
        }
    }

    window.addEventListener("alpha-purchased", handleAlpha)
    return () => window.removeEventListener("alpha-purchased", handleAlpha)
  }, [chartData])

  return (
    <Card className="col-span-4 border-zinc-800 bg-zinc-950/50">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
            <CardTitle className="text-zinc-100">Live Market: {ticker}/USDC</CardTitle>
            <p className="text-2xl font-bold text-emerald-400">${currentPrice.toFixed(4)}</p>
        </div>
        {isLive ? (
            <Badge variant="outline" className="animate-pulse border-emerald-500 text-emerald-500">● LIVE</Badge>
        ) : (
            <Badge variant="outline" className="border-purple-500 text-purple-500">🔮 PREDICTION MODE</Badge>
        )}
      </CardHeader>
      <CardContent className="pl-0">
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorPred" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                </linearGradient>
              </defs>
              
              <XAxis dataKey="time" stroke="#52525b" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis 
                stroke="#52525b" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false} 
                domain={['auto', 'auto']}
                tickFormatter={(val) => `$${val}`} 
              />
              <Tooltip 
                contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a" }}
                labelStyle={{ color: "#a1a1aa" }}
              />
              
              {/* Historical Data (Green) */}
              <Area 
                type="monotone" 
                dataKey="price" 
                stroke="#10b981" 
                strokeWidth={2}
                fill="url(#colorPrice)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

export default TradingView
