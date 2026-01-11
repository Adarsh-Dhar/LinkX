"use client"

import { Home, ShoppingBag, Terminal, MessageCircle, TrendingUp, Zap } from "lucide-react"

interface SidebarProps {
  currentPage: string
  onNavigate: (page: string) => void
}

export default function Sidebar({ currentPage, onNavigate }: SidebarProps) {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: Home },
    { id: "chat", label: "Agent Chat", icon: MessageCircle },
    { id: "marketplace", label: "Alpha Market", icon: ShoppingBag },
    { id: "trading", label: "Trading", icon: TrendingUp },
    { id: "simulation", label: "Simulation", icon: Zap },
    { id: "terminal", label: "Live Terminal", icon: Terminal },
  ]

  return (
    <aside className="w-64 glass border-r border-border/30 flex flex-col">
      <div className="p-6 border-b border-border/30">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-primary via-accent to-secondary bg-clip-text text-transparent">
          Alpha
        </h1>
        <p className="text-xs text-muted-foreground mt-1">Consumer AI</p>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = currentPage === item.id
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? "bg-gradient-to-r from-primary to-accent text-white glow-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-card/50"
              }`}
            >
              <Icon size={20} />
              <span className="text-sm font-medium">{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className="p-4 border-t border-border/30 text-xs text-muted-foreground">
        <p>v0.2.0</p>
      </div>
    </aside>
  )
}
