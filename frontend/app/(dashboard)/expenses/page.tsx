"use client";

import TopBar from "@/components/TopBar";
import { useExpenses, useBurnRate } from "@/hooks/useFinancialData";
import { useAppStore } from "@/lib/store";
import { formatCurrency, formatCompactNumber, cn } from "@/lib/utils";
import {
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Receipt,
  Sparkles,
  Filter,
  Download,
  Search,
  Zap,
  Tag,
  Calendar,
  Layers,
  MoreVertical,
  Users,
  Globe,
  Shield,
} from "lucide-react";

export default function ExpensesPage() {
  const { expenses, isLoading } = useExpenses();
  const { burnRate } = useBurnRate();
  const { openChat } = useAppStore();

  const totalExpenses = Object.values(expenses.breakdown as Record<string, number>).reduce((a: number, b: number) => a + b, 0);

  const categories = [
    { name: "Payroll", key: "payroll", color: "#6366f1", icon: <Users className="w-5 h-5" /> },
    { name: "Infrastructure", key: "aws", color: "#0ea5e9", icon: <Globe className="w-5 h-5" /> },
    { name: "Operations", key: "saas", color: "#8b5cf6", icon: <Layers className="w-5 h-5" /> },
    { name: "Marketing", key: "marketing", color: "#ec4899", icon: <Zap className="w-5 h-5" /> },
    { name: "General", key: "office", color: "#10b981", icon: <Tag className="w-5 h-5" /> },
    { name: "Compliance", key: "legal", color: "#f59e0b", icon: <Shield className="w-5 h-5" /> },
  ];

  return (
    <div className="min-h-screen bg-slate-950 pb-20">
      <TopBar title="Capital Allocations" />

      <div className="p-8 space-y-10 max-w-[1600px] mx-auto">
        {/* Header Section */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-bold uppercase tracking-wider">
              <Receipt className="w-3.5 h-3.5" />
              Internal Ledger Verified
            </div>
            <h1 className="text-4xl font-black text-white tracking-tight font-outfit uppercase">
              Expense <span className="text-slate-500">Analysis</span>
            </h1>
            <div className="flex items-center gap-4 text-slate-500 font-bold text-[10px] uppercase tracking-widest">
              <div className="flex items-center gap-2">
                <Layers className="w-3.5 h-3.5" />
                <span>Total Outflow: {formatCurrency(totalExpenses)}</span>
              </div>
              <div className="w-1.5 h-1.5 rounded-full bg-slate-800" />
              <div className="flex items-center gap-2 text-emerald-500">
                <Shield className="w-3.5 h-3.5" />
                <span>Status: AUDITED</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button className="btn-secondary text-xs">
              <Download className="w-4 h-4" />
              Download Ledger
            </button>
            <button
              onClick={() => openChat("Optimize expenditures")}
              className="btn-primary text-xs flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              AI Leakage Audit
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { title: "Net Burn", value: formatCurrency(totalExpenses), icon: Receipt, trend: "Current Cycle", trendColor: "text-slate-400" },
            { title: "Payroll Lever", value: "Primary", icon: Users, trend: "64% of OpEx", trendColor: "text-indigo-400" },
            { title: "Velocity Alert", value: "Cloud Ops", icon: TrendingUp, trend: "+8% Spike", trendColor: "text-rose-500" },
            { title: "Annual Burn", value: formatCurrency(totalExpenses * 12), icon: Calendar, trend: "Projected", trendColor: "text-slate-400" },
          ].map((stat, i) => (
            <div key={i} className="bg-slate-900 border border-white/10 p-6 rounded-2xl group hover:border-indigo-500/30 transition-all">
              <div className="flex items-center justify-between mb-4">
                <div className="p-2 rounded-lg bg-white/5 text-slate-400 group-hover:text-indigo-400 transition-colors">
                  <stat.icon className="w-5 h-5" />
                </div>
                <span className={`text-[10px] font-bold uppercase tracking-wider ${stat.trendColor}`}>{stat.trend}</span>
              </div>
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{stat.title}</span>
                <div className="text-2xl font-black text-white font-outfit uppercase tracking-tight">{stat.value}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
          {/* Expense Breakdown */}
          <div className="xl:col-span-8 space-y-8">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white font-outfit uppercase tracking-tighter">Expenditure Matrix</h2>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-0.5">Categorical Efficiency Breakdowns</p>
              </div>
              <div className="relative group">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-600 group-focus-within:text-indigo-400" />
                <input
                  placeholder="Search categories..."
                  className="pl-12 pr-6 py-2.5 bg-slate-900 border border-white/10 rounded-xl text-[10px] font-bold uppercase tracking-wider focus:outline-none focus:border-indigo-500/50 w-64 transition-all text-white placeholder-slate-600"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {categories.map((cat) => {
                const amount = expenses.breakdown[cat.key] || 0;
                const percentage = totalExpenses > 0 ? (amount / totalExpenses) * 100 : 0;
                const trend = expenses.trend?.find((t) => t.category === cat.key)?.trend || 0;

                return (
                  <div
                    key={cat.key}
                    className="bg-slate-900 border border-white/10 p-8 rounded-2xl group hover:border-indigo-500/30 transition-all"
                  >
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-white/5 border border-white/10 rounded-xl text-slate-400 group-hover:text-indigo-400 transition-all">
                          {cat.icon}
                        </div>
                        <div>
                          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block mb-0.5">Allocation</span>
                          <span className="text-lg font-bold text-white tracking-tight uppercase font-outfit">
                            {cat.name}
                          </span>
                        </div>
                      </div>
                      <div className={cn(
                        "px-3 py-1 rounded-lg text-[9px] font-bold uppercase tracking-wider border",
                        trend > 0 ? "text-rose-500 bg-rose-500/5 border-rose-500/10" : "text-emerald-500 bg-emerald-500/5 border-emerald-500/10"
                      )}>
                        {trend > 0 ? "Rise" : "Fall"} {Math.abs(trend)}%
                      </div>
                    </div>

                    <div className="space-y-4">
                      <p className="text-3xl font-black text-white font-outfit tracking-tight">
                        {formatCurrency(amount)}
                      </p>
                      <div className="space-y-2">
                        <div className="flex justify-between text-[9px] font-bold uppercase tracking-widest text-slate-500">
                          <span>Mix Utilization</span>
                          <span className="text-white">{percentage.toFixed(0)}%</span>
                        </div>
                        <div className="h-1.5 bg-slate-950 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-1000"
                            style={{ width: `${percentage}%`, backgroundColor: cat.color }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Side Actions */}
          <div className="xl:col-span-4 space-y-8">
            {/* AI Alert Cube */}
            <div className="bg-indigo-600 rounded-3xl p-8 text-white relative shadow-xl overflow-hidden group">
              <Zap className="absolute -right-8 -bottom-8 w-40 h-40 opacity-10 rotate-12" />
              <h2 className="text-xl font-black font-outfit uppercase tracking-tight mb-4 flex items-center gap-2">
                <Receipt className="w-5 h-5" />
                Burn Logic
              </h2>
              <p className="text-sm font-medium leading-relaxed mb-10 opacity-90">
                Infrastructure costs (Cloud Ops) spiked 12.5%. Vireon AI recommends an immediate resource optimization audit.
              </p>
              <button
                onClick={() => openChat("Cloud Ops optimization audit")}
                className="w-full py-4 bg-white text-indigo-700 text-[10px] font-black uppercase tracking-[0.2em] rounded-xl hover:bg-slate-100 transition-all font-outfit"
              >
                Initiate Protocol
              </button>
            </div>

            {/* Recent Outflow */}
            <div className="bg-slate-900 border border-white/10 rounded-3xl p-8">
              <h3 className="text-lg font-bold text-white font-outfit uppercase tracking-tight mb-8 text-center">Recent Outflow Matrix</h3>
              <div className="space-y-6">
                {[
                  { vendor: "AWS Cloud", category: "Infra", date: "MAR 18", amount: 8450 },
                  { vendor: "Figma Ops", category: "Saas", date: "MAR 17", amount: 525 },
                  { vendor: "Gusto Payroll", category: "Ops", date: "MAR 15", amount: 42000 },
                  { vendor: "Stripe Fees", category: "Fin", date: "MAR 14", amount: 1240 },
                ].map((tx, i) => (
                  <div key={i} className="flex items-center justify-between group cursor-pointer">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-slate-800 border border-white/5 rounded-xl flex items-center justify-center text-slate-500 group-hover:text-indigo-400 transition-all">
                        <ArrowDownRight className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="text-[11px] font-bold text-white uppercase tracking-wider">{tx.vendor}</p>
                        <p className="text-[9px] font-medium text-slate-600 uppercase tracking-widest mt-0.5">{tx.category} • {tx.date}</p>
                      </div>
                    </div>
                    <p className="text-xs font-bold text-slate-400 group-hover:text-white">
                      {formatCompactNumber(tx.amount)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
