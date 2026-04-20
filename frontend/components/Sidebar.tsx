"use client";

import { cn } from "@/lib/utils";
import {
  LayoutDashboard, AlertTriangle, TrendingUp, CreditCard, BarChart3,
  Settings, ChevronLeft, ChevronRight, ShieldCheck, Wallet, Receipt,
  LineChart, Bot, Landmark, Cpu, Workflow, Users, FlameKindling,
  BookOpen, Calculator, Activity, ShieldAlert, Building2, ClipboardList,
  FileText, ShoppingCart, UserCheck, Package, PieChart, Scale,
  Calendar, GitBranch, Layers, DollarSign, Globe,
  ChevronDown, ChevronUp,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAppStore } from "@/lib/store";
import { Logo } from "./Logo";
import { useState } from "react";

type NavItem = { name: string; path: string; icon: React.ElementType };
type NavSection = { title: string; items: NavItem[] };

const navSections: NavSection[] = [
  {
    title: "Core",
    items: [
      { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
      { name: "AI CFO Agent", path: "/agent", icon: Bot },
      { name: "Features", path: "/features", icon: Layers },
    ],
  },
  {
    title: "Transactions",
    items: [
      { name: "Invoices", path: "/invoices", icon: FileText },
      { name: "Bills & AP", path: "/bills", icon: Receipt },
      { name: "Expenses", path: "/expenses", icon: CreditCard },
      { name: "Revenue", path: "/revenue", icon: TrendingUp },
      { name: "Procurement", path: "/procurement", icon: ShoppingCart },
    ],
  },
  {
    title: "Accounting",
    items: [
      { name: "Chart of Accounts", path: "/chart-of-accounts", icon: Scale },
      { name: "Reports", path: "/reports", icon: BarChart3 },
      { name: "Budget", path: "/budget", icon: PieChart },
      { name: "Assets", path: "/assets", icon: Landmark },
      { name: "Payroll", path: "/payroll", icon: Users },
    ],
  },
  {
    title: "Cash & Risk",
    items: [
      { name: "Cash Flow", path: "/cash-flow", icon: Wallet },
      { name: "Burn Analysis", path: "/burn-analysis", icon: FlameKindling },
      { name: "Runway", path: "/runway", icon: LineChart },
      { name: "Cash Flow at Risk", path: "/cfar", icon: Activity },
      { name: "Scenarios", path: "/scenarios", icon: GitBranch },
    ],
  },
  {
    title: "Startup Metrics",
    items: [
      { name: "SaaS Metrics", path: "/saas-metrics", icon: TrendingUp },
      { name: "Equity & Cap Table", path: "/equity", icon: DollarSign },
      { name: "Investor Portal", path: "/investor", icon: ShieldCheck },
      { name: "Benchmarking", path: "/benchmarking", icon: Globe },
    ],
  },
  {
    title: "Relationships",
    items: [
      { name: "Customers", path: "/customers", icon: UserCheck },
      { name: "Vendors", path: "/vendors", icon: Package },
      { name: "Collections", path: "/collections", icon: CreditCard },
    ],
  },
  {
    title: "Compliance",
    items: [
      { name: "Compliance Calendar", path: "/compliance", icon: Calendar },
      { name: "Tax", path: "/tax", icon: Landmark },
      { name: "Tax Provisioning", path: "/tax-provisioning", icon: Calculator },
      { name: "Month-End Close", path: "/month-end-close", icon: ClipboardList },
      { name: "Accruals", path: "/accruals", icon: BookOpen },
    ],
  },
  {
    title: "Intelligence",
    items: [
      { name: "Anomalies", path: "/anomalies", icon: AlertTriangle },
      { name: "Vendor Risk", path: "/vendor-risk", icon: ShieldAlert },
      { name: "Consolidation", path: "/consolidation", icon: Building2 },
      { name: "Operations", path: "/operations", icon: Workflow },
      { name: "CTO Planner", path: "/dashboard/cto", icon: Cpu },
    ],
  },
  {
    title: "System",
    items: [
      { name: "Settings", path: "/settings", icon: Settings },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarExpanded, toggleSidebar, user } = useAppStore();
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(
    new Set(["Intelligence", "System"])
  );

  const toggleSection = (title: string) => {
    setCollapsedSections((prev) => {
      const next = new Set(prev);
      if (next.has(title)) next.delete(title);
      else next.add(title);
      return next;
    });
  };

  return (
    <aside
      className={cn(
        "bg-[#fcf8f2]/90 backdrop-blur-3xl border-r border-[#e3d6c7] flex flex-col transition-all duration-500 ease-in-out relative z-40 group/sidebar h-screen sticky top-0",
        sidebarExpanded ? "w-72" : "w-20"
      )}
    >
      {/* Header */}
      <div className="h-20 flex items-center px-6 border-b border-[#e3d6c7] shrink-0">
        <Logo showText={sidebarExpanded} size={sidebarExpanded ? "md" : "sm"} variant="gradient" className="transition-all duration-300" />
      </div>

      {/* Toggle */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-24 w-6 h-6 bg-[#1f1a16] border border-[#d8cabc] rounded-full flex items-center justify-center text-[#fff7ef] shadow-lg hover:scale-110 active:scale-95 transition-all z-50 opacity-0 group-hover/sidebar:opacity-100"
      >
        {sidebarExpanded ? <ChevronLeft className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
      </button>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 overflow-y-auto no-scrollbar space-y-1">
        {navSections.map((section) => {
          const isCollapsed = collapsedSections.has(section.title);
          return (
            <div key={section.title} className="mb-2">
              {sidebarExpanded && (
                <button
                  onClick={() => toggleSection(section.title)}
                  className="w-full flex items-center justify-between px-3 py-1.5 mb-1 group/sec"
                >
                  <span className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500 group-hover/sec:text-slate-700 transition-colors">
                    {section.title}
                  </span>
                  {isCollapsed
                    ? <ChevronDown className="w-3 h-3 text-slate-400" />
                    : <ChevronUp className="w-3 h-3 text-slate-400" />}
                </button>
              )}
              {(!isCollapsed || !sidebarExpanded) && (
                <div className="space-y-0.5">
                  {section.items.map((item) => {
                    const isActive = pathname === item.path || pathname.startsWith(item.path + "/");
                    return (
                      <Link
                        key={item.name}
                        href={item.path}
                        className={cn(
                          "flex items-center gap-3 px-3 py-2.5 rounded-[14px] transition-all duration-300 group font-medium relative",
                          isActive
                            ? "bg-[#f4e7d8] text-[#211d19] border border-[#d6c2ad]"
                            : "text-[#6a6054] hover:text-[#1f1a16] hover:bg-white/60 hover:border-[#e4d7c9] border border-transparent"
                        )}
                        title={!sidebarExpanded ? item.name : undefined}
                      >
                        <item.icon className={cn(
                          "w-4.5 h-4.5 shrink-0 transition-all duration-300",
                          isActive ? "text-[#8d4f27] scale-110" : "group-hover:scale-110 group-hover:text-[#8d4f27]"
                        )} />
                        {sidebarExpanded && (
                          <span className="text-[11px] font-bold tracking-wide truncate">
                            {item.name}
                          </span>
                        )}
                        {isActive && (
                          <div className="absolute left-0 w-0.5 h-5 bg-[#b3622d] rounded-r-full" />
                        )}
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* User */}
      <div className="p-4 border-t border-[#e3d6c7] bg-white/55 backdrop-blur-3xl shrink-0">
        <div className={cn(
          "flex items-center gap-3 p-3 rounded-[18px] bg-white/75 border border-[#e4d8cb] hover:bg-white group/user cursor-pointer transition-all",
          !sidebarExpanded && "justify-center px-2"
        )}>
          <div className="relative shrink-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#2c2520] to-[#4c3a2d] flex items-center justify-center text-[#fff7ef] font-black text-xs shadow-xl ring-1 ring-[#d9cab9] group-hover/user:scale-105 transition-transform">
              {user?.name?.split(" ").map((n: string) => n[0]).join("") || "AD"}
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-[#ce6f35] border-2 border-[#fcf8f2] rounded-full shadow" />
          </div>
          {sidebarExpanded && (
            <div className="flex flex-col min-w-0 flex-1">
              <span className="text-[11px] font-black text-[#1f1a16] truncate uppercase tracking-tight">
                {user?.name || "Aditi Singh"}
              </span>
              <span className="text-[9px] font-black text-[#8d4f27] uppercase tracking-widest bg-[#f6e7d7] px-1.5 py-0.5 rounded-md mt-0.5 self-start">
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
