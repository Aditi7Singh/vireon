"use client";

import { cn } from "@/lib/utils";
import { 
  LayoutDashboard, 
  AlertTriangle, 
  TrendingUp, 
  CreditCard, 
  BarChart3, 
  Settings, 
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Zap,
  HelpCircle,
  Wallet,
  Receipt,
  LineChart,
  Bot,
  LogOut
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAppStore } from "@/lib/store";
import { Logo } from "./Logo";

const navItems = [
  { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
  { name: "Runway", path: "/runway", icon: Wallet },
  { name: "Expenses", path: "/expenses", icon: Receipt },
  { name: "Revenue", path: "/revenue", icon: BarChart3 },
  { name: "Scenarios", path: "/scenarios", icon: LineChart },
  { name: "Benchmarking", path: "/benchmarking", icon: TrendingUp },
  { name: "AI Agent", path: "/agent", icon: Bot },
  { name: "Anomalies", path: "/anomalies", icon: AlertTriangle },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarExpanded, toggleSidebar, user, alertCount } = useAppStore();

  return (
    <aside
      className={cn(
        "bg-slate-950 border-r border-slate-800/50 flex flex-col transition-all duration-500 ease-in-out relative z-40 group/sidebar shadow-2xl shadow-indigo-500/5 h-screen sticky top-0",
        sidebarExpanded ? "w-64" : "w-20"
      )}
    >
      {/* Header / Logo */}
      <div className="h-20 flex items-center px-6 border-b border-slate-800/50">
        <Logo 
          showText={sidebarExpanded} 
          size={sidebarExpanded ? "md" : "sm"} 
          variant="white"
          className="transition-all duration-300"
        />
      </div>

      {/* Toggle Button - Float Style */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-24 w-6 h-6 bg-indigo-600 border border-indigo-500 rounded-full flex items-center justify-center text-white shadow-lg hover:scale-110 active:scale-95 transition-all z-50 opacity-0 group-hover/sidebar:opacity-100"
      >
        {sidebarExpanded ? <ChevronLeft className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
      </button>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-8 space-y-2 overflow-y-auto no-scrollbar">
        {sidebarExpanded && (
          <p className="px-3 text-[10px] font-black uppercase tracking-widest text-slate-500 mb-4">
            Main Intelligence
          </p>
        )}
        {navItems.map((item) => {
          const isActive = pathname === item.path || pathname.startsWith(item.path + "/");
          return (
            <Link
              key={item.name}
              href={item.path}
              className={cn(
                "flex items-center gap-3 px-3.5 py-3 rounded-2xl transition-all duration-300 group font-medium relative",
                isActive
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
                  : "text-slate-400 hover:text-white hover:bg-slate-900"
              )}
            >
              <item.icon className={cn(
                "w-5 h-5 transition-transform duration-300",
                isActive ? "scale-110" : "group-hover:scale-110"
              )} />
              
              {sidebarExpanded && (
                <span className="text-sm font-bold tracking-tight">
                  {item.name}
                </span>
              )}

              {/* Tooltip for collapsed state */}
              {!sidebarExpanded && (
                <div className="absolute left-full ml-4 px-3 py-1.5 bg-slate-900 border border-slate-700 text-white text-[10px] font-bold rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap shadow-xl z-50">
                   {item.name}
                </div>
              )}

              {/* Anomaly Badge */}
              {item.name === "Anomalies" && alertCount > 0 && (
                <span className={cn(
                  "absolute flex items-center justify-center min-w-5 h-5 px-1.5 text-[10px] font-black rounded-full transition-all duration-300",
                  sidebarExpanded ? "right-4" : "right-1.5 -top-1",
                  isActive ? "bg-white text-indigo-600" : "bg-rose-500 text-white"
                )}>
                  {alertCount}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* User & Bottom Section */}
      <div className="p-4 border-t border-slate-800/50 bg-slate-950/50 backdrop-blur-md space-y-4">
        <Link
          href="/settings"
          className={cn(
            "flex items-center gap-3 px-3.5 py-3 rounded-2xl transition-all duration-300 text-slate-400 hover:text-white hover:bg-slate-900 group relative",
            pathname === "/settings" && "bg-slate-900 text-white"
          )}
        >
          <Settings className="w-5 h-5 group-hover:rotate-90 transition-transform duration-500" />
          {sidebarExpanded && <span className="text-sm font-bold tracking-tight">Settings</span>}
          {!sidebarExpanded && (
            <div className="absolute left-full ml-4 px-3 py-1.5 bg-slate-900 border border-slate-700 text-white text-[10px] font-bold rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap shadow-xl z-50">
               Settings
            </div>
          )}
        </Link>

        {/* User Card */}
        <div className={cn(
          "flex items-center gap-3 p-3 rounded-2xl bg-slate-900/50 border border-slate-800 transition-all duration-300 hover:bg-slate-900 group/user relative",
          !sidebarExpanded && "justify-center px-2"
        )}>
          <div className="relative">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white font-black text-xs shadow-xl ring-2 ring-slate-800 ring-offset-2 ring-offset-slate-950 transition-transform group-hover/user:scale-105">
              {user?.name?.split(" ").map((n: string) => n[0]).join("") || "AD"}
            </div>
            <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-emerald-500 border-2 border-slate-950 rounded-full shadow-lg" />
          </div>
          {sidebarExpanded && (
            <div className="flex flex-col min-w-0 flex-1">
              <span className="text-xs font-black text-white truncate font-outfit leading-none">
                {user?.name || "Aditi Singh"}
              </span>
              <span className="text-[9px] text-slate-500 font-bold uppercase tracking-widest truncate mt-1">
                {user?.role || "FOUNDER"}
              </span>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
