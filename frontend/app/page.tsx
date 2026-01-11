"use client"

import { useState } from "react"
import Sidebar from "@/components/sidebar"
import TopBar from "@/components/topbar"
import Dashboard from "@/components/dashboard"
import AlphaMarketplace from "@/components/alpha-marketplace"
import LiveTerminal from "@/components/live-terminal"
import TradingView from "@/components/trading-view"
import TradingDashboard from "@/components/trading-dashboard"
import SimulationView from "@/components/simulation-view"
import ChatPage from "@/app/chat/page"
import TradingPanel from "@/components/trading-panel"

export default function Home() {
  const [currentPage, setCurrentPage] = useState("dashboard")

  const renderPage = () => {
    switch (currentPage) {
      case "dashboard":
        return <Dashboard />
      case "chat":
        return <ChatPage />
      case "marketplace":
        return <AlphaMarketplace />
      case "terminal":
        return <LiveTerminal />
      case "trading":
        return <TradingDashboard />
      case "simulation":
        return <SimulationView autoUpdate={true} />
      case "charts":
        return <TradingView />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-auto bg-black/40">
          {renderPage()}
        </main>
      </div>
      {(currentPage === "simulation" || currentPage === "trading") && <TradingPanel />}
    </div>
  )
}
