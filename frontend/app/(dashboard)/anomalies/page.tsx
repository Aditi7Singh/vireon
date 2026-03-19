"use client";

import TopBar from "@/components/TopBar";
import { useAlerts } from "@/hooks/useFinancialData";
import { Alert } from "@/lib/api";
import { formatCurrency, formatRelativeTime, cn } from "@/lib/utils";
import {
  AlertTriangle,
  AlertCircle,
  Info,
  XCircle,
  CheckCircle2,
  ChevronDown,
  Filter,
  RefreshCw,
  Sparkles,
  Zap,
  ArrowRight,
  ShieldCheck,
  Search,
} from "lucide-react";
import { useState } from "react";
import { useAppStore } from "@/lib/store";

export default function AnomaliesPage() {
  const { alerts, isLoading, mutate } = useAlerts();
  const { openChat, isSyncing, setIsSyncing } = useAppStore();
  const [filter, setFilter] = useState<"all" | "critical" | "warning" | "info">("all");

  const filteredAlerts: Alert[] = alerts?.alerts?.filter(
    (alert: Alert) => filter === "all" || alert.severity === filter
  ) ?? [];

  const handleScan = async () => {
    setIsSyncing(true);
    await new Promise((resolve) => setTimeout(resolve, 3000));
    setIsSyncing(false);
    mutate();
  };

  return (
    <div className="min-h-screen bg-slate-950 pb-20">
      <TopBar title="Anomaly Detection" />

      <div className="p-8 space-y-10 max-w-[1600px] mx-auto">
        {/* Header Section */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8">
          <div className="space-y-4">
            <h1 className="text-4xl font-bold text-white tracking-tight">
              Audit <span className="text-slate-400">& Compliance</span>
            </h1>
            <div className="flex items-center gap-4 text-slate-500 font-medium text-xs">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                <span>Sentinel Core: Active</span>
              </div>
              <div className="w-1 h-1 rounded-full bg-slate-700" />
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                <span>Ledger Synchronized</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={handleScan}
              disabled={isSyncing}
              className="btn-secondary"
            >
              <RefreshCw className={cn("w-4 h-4", isSyncing && "animate-spin")} />
              {isSyncing ? "Scanning..." : "Run Scan"}
            </button>
            <button
              onClick={() => openChat("Deep Forensic Analysis Request")}
              className="btn-primary"
            >
              <Sparkles className="w-4 h-4" />
              Ask AI Agent
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { title: "Efficiency Score", value: "98.5%", desc: "Standard Range", icon: ShieldCheck, color: "emerald" },
            { title: "Active Alerts", value: alerts?.total ?? 0, desc: "Pending Review", icon: AlertCircle, color: "slate" },
            { title: "High Priority", value: alerts?.critical_count ?? 0, desc: "Immediate Action", icon: XCircle, color: "rose" },
            { title: "Potential Savings", value: "$4.8K", desc: "Projected Recovery", icon: RefreshCw, color: "indigo" },
          ].map((stat, i) => (
            <div key={i} className="glass-card p-6 rounded-2xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center border border-slate-700",
                    stat.color === 'rose' && "text-rose-500",
                    stat.color === 'emerald' && "text-emerald-500",
                    stat.color === 'indigo' && "text-indigo-500",
                  )}>
                    <stat.icon className="h-4 w-4" />
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{stat.title}</span>
                </div>
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">{stat.value}</div>
              <p className="text-[10px] font-medium text-slate-500 mt-1 uppercase tracking-wider">{stat.desc}</p>
            </div>
          ))}
        </div>

        {/* List Section */}
        <div className="space-y-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div className="flex items-center p-1 bg-slate-900 border border-slate-800 rounded-lg">
              {(["all", "critical", "warning", "info"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={cn(
                    "px-4 py-1.5 text-[10px] font-bold uppercase tracking-wider rounded transition-all",
                    filter === f
                      ? "bg-indigo-600 text-white shadow-lg"
                      : "text-slate-500 hover:text-slate-300"
                  )}
                >
                  {f}
                </button>
              ))}
            </div>

            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                placeholder="Search alerts..."
                className="pl-12 pr-4 py-2.5 text-xs bg-slate-900 border border-slate-800 rounded-lg focus:outline-none focus:border-indigo-500/50 w-full sm:w-64 transition-all text-white placeholder-slate-600"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {filteredAlerts.map((alert: Alert) => (
              <div
                key={alert.id}
                className="group glass-card rounded-[40px] p-8 lg:p-10 transition-all duration-700 hover:bg-white/[0.03] border-white/5 hover:border-white/10"
              >
                <div className="flex flex-col lg:flex-row lg:items-center gap-10">
                  <div className={cn(
                    "w-20 h-20 shrink-0 rounded-[28px] flex items-center justify-center p-6 border transition-all duration-700 rotate-0 group-hover:rotate-6",
                    alert.severity === 'critical' ? 'bg-rose-500/10 border-rose-500/20 text-rose-500 shadow-[0_0_30px_rgba(244,63,94,0.1)]' :
                      alert.severity === 'warning' ? 'bg-amber-500/10 border-amber-500/20 text-amber-500 shadow-[0_0_30px_rgba(245,158,11,0.1)]' :
                        'bg-indigo-500/10 border-indigo-500/20 text-indigo-500 shadow-[0_0_30px_rgba(99,102,241,0.1)]'
                  )}>
                    {alert.severity === 'critical' ? <XCircle className="w-10 h-10" /> :
                      alert.severity === 'warning' ? <AlertTriangle className="w-10 h-10" /> :
                        <Info className="w-10 h-10" />}
                  </div>

                  <div className="flex-1 space-y-4">
                    <div className="flex items-center gap-4">
                      <span className={cn(
                        "px-4 py-1.5 text-[9px] font-black uppercase tracking-[0.2em] rounded-full border",
                        alert.severity === 'critical' ? 'bg-rose-500/10 border-rose-500/20 text-rose-500' :
                          alert.severity === 'warning' ? 'bg-amber-500/10 border-amber-500/20 text-amber-500' :
                            'bg-indigo-500/10 border-indigo-500/20 text-indigo-500'
                      )}>
                        {alert.severity}
                      </span>
                      <span className="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em]">{alert.alert_type}</span>
                      <div className="w-1.5 h-1.5 rounded-full bg-white/5" />
                      <span className="text-[9px] font-black text-slate-600 uppercase tracking-widest">{formatRelativeTime(alert.created_at)}</span>
                    </div>

                    <h3 className="text-2xl font-black text-white font-outfit tracking-tighter uppercase leading-tight group-hover:text-indigo-400 transition-colors">
                      {alert.description}
                    </h3>

                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-10 pt-4">
                      <DataPoint label="Exposure" value={formatCurrency(alert.amount)} highlight />
                      <DataPoint label="Institutional Baseline" value={formatCurrency(alert.baseline)} />
                      <DataPoint label="Delta Vector" value={`+${alert.delta_pct.toFixed(1)}%`} color="danger" />
                      <DataPoint label="Survival Impact" value={`-${alert.runway_impact.toFixed(1)} MO`} color="danger" />
                    </div>
                  </div>

                  <div className="flex flex-row lg:flex-col items-center gap-4 pt-6 lg:pt-0">
                    <button
                      onClick={() => openChat("Deep audit of anomaly: " + alert.description)}
                      className="flex-1 lg:w-40 px-6 py-4 text-[10px] font-black text-white bg-indigo-600 rounded-2xl hover:bg-indigo-500 shadow-2xl shadow-indigo-600/20 transition-all uppercase tracking-[0.2em] active:scale-95"
                    >
                      Audit with AI
                    </button>
                    <button className="flex-1 lg:w-40 px-6 py-4 text-[10px] font-black text-slate-500 bg-white/5 border border-white/5 rounded-2xl hover:bg-white/10 transition-all uppercase tracking-[0.2em]">
                      Archive Node
                    </button>
                  </div>
                </div>
              </div>
            ))}

            {filteredAlerts.length === 0 && !isLoading && (
              <div className="flex flex-col items-center justify-center py-32 glass-card rounded-[48px] border-dashed border-white/10">
                <div className="w-24 h-24 bg-emerald-500/10 rounded-full flex items-center justify-center mb-10 shadow-[0_0_50px_rgba(16,185,129,0.1)] border border-emerald-500/20">
                  <CheckCircle2 className="w-10 h-10 text-emerald-500" />
                </div>
                <h3 className="text-3xl font-black text-white font-outfit uppercase tracking-tighter">
                  Ledger Clear
                </h3>
                <p className="text-slate-500 mt-4 font-bold text-[10px] uppercase tracking-widest max-w-sm text-center leading-relaxed">
                  Sentinel protocol has not identified any institutional risk factors in the current ledger iteration.
                </p>
                <button onClick={handleScan} className="mt-12 group flex items-center gap-4 text-indigo-400 font-black text-[10px] uppercase tracking-[0.2em] hover:text-white transition-all">
                  Execute Deep Cycle Scan <ArrowRight className="w-4 h-4 group-hover:translate-x-2 transition-transform" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function DataPoint({ label, value, highlight, color }: any) {
  return (
    <div className="space-y-3">
      <p className="text-[9px] font-black text-slate-600 uppercase tracking-[0.2em]">{label}</p>
      <p className={cn(
        "text-lg font-black font-outfit tracking-widest",
        highlight ? "text-white" : "text-slate-500",
        color === 'danger' && "text-rose-500",
        color === 'success' && "text-emerald-500"
      )}>
        {value}
      </p>
    </div>
  );
}

