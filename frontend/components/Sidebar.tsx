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
  LogOut,
  Landmark,
  Grid3X3,
  Cpu,
  Workflow,
  Users
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAppStore } from "@/lib/store";
import { Logo } from "./Logo";

const navItems = [
  { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
  { name: "Feature Hub", path: "/features", icon: Grid3X3 },
  { name: "Operations", path: "/operations", icon: Workflow },
  { name: "CTO Planner", path: "/dashboard/cto", icon: Cpu },
  { name: "Runway", path: "/runway", icon: Wallet },
  { name: "Cash Flow", path: "/cash-flow", icon: Wallet },
  { name: "Collections", path: "/collections", icon: CreditCard },
  { name: "Budget", path: "/budget", icon: BarChart3 },
  { name: "Payroll", path: "/payroll", icon: Users },
  { name: "Assets", path: "/assets", icon: Landmark },
  { name: "Expenses", path: "/expenses", icon: Receipt },
  { name: "Revenue", path: "/revenue", icon: BarChart3 },
  { name: "Tax", path: "/tax", icon: Landmark },
  { name: "Scenarios", path: "/scenarios", icon: LineChart },
  { name: "Benchmarking", path: "/benchmarking", icon: TrendingUp },
  { name: "Investor", path: "/investor", icon: ShieldCheck },
  { name: "AI Agent", path: "/agent", icon: Bot },
  { name: "Anomalies", path: "/anomalies", icon: AlertTriangle },
  { name: "Settings", path: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarExpanded, toggleSidebar, user, alertCount } = useAppStore();

  return (
    <aside
      className={cn(
        "bg-[#fcf8f2]/90 backdrop-blur-3xl border-r border-[#e3d6c7] flex flex-col transition-all duration-500 ease-in-out relative z-40 group/sidebar h-screen sticky top-0",
        sidebarExpanded ? "w-72" : "w-24"
      )}
    >
      {/* Header / Logo */}
      <div className="h-24 flex items-center px-8 border-b border-[#e3d6c7]">
        <Logo
          showText={sidebarExpanded}
          size={sidebarExpanded ? "md" : "sm"}
          variant="gradient"
          className="transition-all duration-300"
        />
      </div>

      {/* Toggle Button - Float Style */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-28 w-6 h-6 bg-[#1f1a16] border border-[#d8cabc] rounded-full flex items-center justify-center text-[#fff7ef] shadow-lg hover:scale-110 active:scale-95 transition-all z-50 opacity-0 group-hover/sidebar:opacity-100"
      >
        {sidebarExpanded ? <ChevronLeft className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
      </button>

      {/* Navigation */}
      <nav className="flex-1 px-6 py-10 space-y-3 overflow-y-auto no-scrollbar">
        {sidebarExpanded && (
          <p className="px-4 text-[9px] font-black uppercase tracking-[0.2em] text-slate-600 mb-6">
            Core Intelligence
          </p>
        )}
        {navItems.map((item) => {
          const isActive = pathname === item.path || pathname.startsWith(item.path + "/");
          return (
            <Link
              key={item.name}
              href={item.path}
              className={cn(
                "flex items-center gap-4 px-4 py-4 rounded-[20px] transition-all duration-500 group font-medium relative",
                isActive
                  ? "bg-[#f4e7d8] text-[#211d19] border border-[#d6c2ad]"
                  : "text-[#6a6054] hover:text-[#1f1a16] hover:bg-white/60 hover:border-[#e4d7c9] border border-transparent"
              )}
            >
              <item.icon className={cn(
                "w-5 h-5 transition-all duration-500",
                isActive ? "text-[#8d4f27] scale-110" : "group-hover:scale-110 group-hover:text-[#8d4f27]"
              )} />

              {sidebarExpanded && (
                <span className="text-xs font-black uppercase tracking-widest">
                  {item.name}
                </span>
              )}

              {isActive && (
                <div className="absolute left-0 w-1 h-6 bg-[#b3622d] rounded-r-full" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* User & Bottom Section */}
      <div className="p-6 border-t border-[#e3d6c7] bg-white/55 backdrop-blur-3xl space-y-4">
        {/* User Card */}
        <div className={cn(
          "flex items-center gap-4 p-4 rounded-[24px] bg-white/75 border border-[#e4d8cb] transition-all duration-500 hover:bg-white group/user relative cursor-pointer",
          !sidebarExpanded && "justify-center px-2"
        )}>
          <div className="relative">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#2c2520] to-[#4c3a2d] flex items-center justify-center text-[#fff7ef] font-black text-xs shadow-xl ring-1 ring-[#d9cab9] transition-transform group-hover/user:scale-105">
              {user?.name?.split(" ").map((n: string) => n[0]).join("") || "AD"}
            </div>
            <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-[#ce6f35] border-2 border-[#fcf8f2] rounded-full shadow-lg" />
          </div>
          {sidebarExpanded && (
            <div className="flex flex-col min-w-0 flex-1">
              <span className="text-[11px] font-black text-[#1f1a16] truncate font-outfit uppercase tracking-tighter">
                {user?.name || "Aditi Singh"}
              </span>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="text-[8px] font-black text-[#8d4f27] uppercase tracking-widest truncate bg-[#f6e7d7] px-1.5 py-0.5 rounded-md">
                  {user?.role || "FOUNDER"}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
