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

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "critical":
        return <XCircle className="w-5 h-5 text-rose-500" />;
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      default:
        return <Info className="w-5 h-5 text-indigo-500" />;
    }
  };

  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case "critical":
        return {
          badge: "bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400 border-rose-200 dark:border-rose-500/20",
          accent: "rose",
        };
      case "warning":
        return {
          badge: "bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400 border-amber-200 dark:border-amber-500/20",
          accent: "amber",
        };
      default:
        return {
          badge: "bg-indigo-100 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-400 border-indigo-200 dark:border-indigo-500/20",
          accent: "indigo",
        };
    }
  };

  const handleScan = async () => {
    setIsSyncing(true);
    await new Promise((resolve) => setTimeout(resolve, 3000));
    setIsSyncing(false);
    mutate();
  };

  return (
    <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950/50">
      <TopBar title="Intelligence & Anomalies" />

      <div className="p-8 space-y-8 max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
          <div className="space-y-1">
            <h1 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight font-outfit">
               Intelligence
            </h1>
            <div className="flex items-center gap-2 text-slate-500 font-medium text-sm">
               <Zap className="w-4 h-4 text-indigo-500" />
               <span>Continuously monitoring transactions for risk</span>
               <span className="w-1 h-1 rounded-full bg-slate-300" />
               <span className="text-emerald-500 font-bold">Neural Scan Online</span>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
             <button
                onClick={handleScan}
                disabled={isSyncing}
                className="flex items-center gap-2 px-5 py-3 text-sm font-bold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-all shadow-sm disabled:opacity-50"
             >
                <RefreshCw className={cn("w-4 h-4", isSyncing && "animate-spin")} />
                {isSyncing ? "Scanning Records..." : "Scan Ledger"}
             </button>
             <button 
                onClick={() => openChat("Intelligence & Anomalies")}
                className="flex items-center gap-2 px-6 py-3 text-sm font-bold text-white bg-indigo-600 rounded-2xl hover:bg-indigo-500 transition-all shadow-xl shadow-indigo-500/25 active:scale-95"
             >
                <Sparkles className="w-4 h-4" />
                Explain with AI
             </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
           <IntelligenceStat 
              title="Identity Score"
              value="98.5%"
              desc="Asset Verification"
              icon={ShieldCheck}
              status="success"
           />
           <IntelligenceStat 
              title="Total Alerts"
              value={alerts?.total ?? 0}
              desc="Across 4 categories"
              icon={AlertCircle}
              status="neutral"
           />
           <IntelligenceStat 
              title="Critical Risks"
              value={alerts?.critical_count ?? 0}
              desc="Requires immediate review"
              icon={XCircle}
              status="danger"
           />
           <IntelligenceStat 
              title="Duplicate Risk"
              value="$1.2k"
              desc="Potential savings"
              icon={RefreshCw}
              status="warning"
           />
        </div>

        {/* Filter & List Section */}
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
             <div className="flex items-center p-1 bg-slate-200/50 dark:bg-slate-900/50 rounded-2xl w-fit">
                {(["all", "critical", "warning", "info"] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={cn(
                      "px-5 py-2 text-xs font-black uppercase tracking-widest rounded-xl transition-all",
                      filter === f
                        ? "bg-white dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 shadow-sm"
                        : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                    )}
                  >
                    {f}
                  </button>
                ))}
             </div>
             
             <div className="relative group">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                <input 
                   placeholder="Search anomalies..."
                   className="pl-10 pr-4 py-2.5 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 w-full sm:w-64 transition-all"
                />
             </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {filteredAlerts.map((alert: Alert) => {
              const styles = getSeverityStyles(alert.severity);
              
              return (
                <div
                  key={alert.id}
                  className="group bg-white dark:bg-slate-900/40 backdrop-blur-sm rounded-[32px] border border-slate-200 dark:border-slate-800/50 p-6 lg:p-8 transition-all hover:border-indigo-500/30 hover:shadow-2xl hover:shadow-indigo-500/5"
                >
                  <div className="flex flex-col lg:flex-row lg:items-center gap-8">
                    <div className={cn(
                      "w-16 h-16 shrink-0 rounded-2xl flex items-center justify-center p-4 ring-8 transition-transform group-hover:scale-110",
                      alert.severity === 'critical' ? 'bg-rose-500 text-white ring-rose-500/10' :
                      alert.severity === 'warning' ? 'bg-amber-500 text-white ring-amber-500/10' :
                      'bg-indigo-500 text-white ring-indigo-500/10'
                    )}>
                      {getSeverityIcon(alert.severity)}
                    </div>
                    
                    <div className="flex-1 space-y-2">
                       <div className="flex items-center gap-2">
                          <span className={cn("px-2.5 py-1 text-[10px] font-black uppercase tracking-widest rounded-lg border", styles.badge)}>
                             {alert.severity}
                          </span>
                          <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{alert.alert_type}</span>
                          <span className="w-1 h-1 rounded-full bg-slate-400 opacity-30" />
                          <span className="text-xs font-bold text-slate-400">{formatRelativeTime(alert.created_at)}</span>
                       </div>
                       
                       <h3 className="text-xl font-black text-slate-900 dark:text-white font-outfit tracking-tight leading-tight">
                         {alert.description}
                       </h3>
                       
                       <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 pt-2">
                          <DataPoint label="Amount" value={formatCurrency(alert.amount)} highlight />
                          <DataPoint label="Baseline" value={formatCurrency(alert.baseline)} />
                          <DataPoint label="Growth" value={`+${alert.delta_pct.toFixed(1)}%`} color="danger" />
                          <DataPoint label="Runway Impact" value={`-${alert.runway_impact.toFixed(1)} mo`} color="danger" />
                       </div>
                    </div>

                    <div className="flex flex-row lg:flex-col items-center gap-2 pt-4 lg:pt-0">
                      <button
                        onClick={() => openChat("Anomaly Analysis: " + alert.description)}
                        className="flex-1 lg:w-32 px-4 py-2.5 text-xs font-black text-white bg-indigo-600 rounded-xl hover:bg-indigo-500 shadow-lg shadow-indigo-600/10 transition-all uppercase tracking-widest"
                      >
                        Ask AI
                      </button>
                      <button className="flex-1 lg:w-32 px-4 py-2.5 text-xs font-black text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition-all uppercase tracking-widest">
                        Dismiss
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}

            {filteredAlerts.length === 0 && !isLoading && (
              <div className="flex flex-col items-center justify-center py-20 bg-white/50 dark:bg-slate-900/20 backdrop-blur-sm rounded-[40px] border border-dashed border-slate-300 dark:border-slate-800">
                <div className="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center mb-6">
                  <CheckCircle2 className="w-10 h-10 text-emerald-500" />
                </div>
                <h3 className="text-2xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">
                  No Intel Found
                </h3>
                <p className="text-slate-500 mt-2 font-medium max-w-sm text-center">
                  {filter === "all"
                    ? "Our neural engine hasn't detected any significant financial risks in the current ledger."
                    : `No ${filter} level intelligence reports available at this moment.`}
                </p>
                <button onClick={handleScan} className="mt-8 flex items-center gap-2 text-indigo-600 font-black text-xs uppercase tracking-widest hover:gap-3 transition-all">
                   Run deep ledger scan <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function IntelligenceStat({ title, value, desc, icon: Icon, status }: any) {
  const statusStyles: any = {
    success: "bg-emerald-500/10 text-emerald-500",
    danger: "bg-rose-500/10 text-rose-500",
    warning: "bg-amber-500/10 text-amber-500",
    neutral: "bg-indigo-500/10 text-indigo-500",
  };

  return (
    <div className="bg-white dark:bg-slate-900/40 backdrop-blur-sm rounded-[32px] border border-slate-200 dark:border-slate-800/50 p-6 group transition-all hover:border-indigo-500/20">
      <div className="flex items-start justify-between">
        <div className={cn("p-3 rounded-2xl transition-transform group-hover:scale-110", statusStyles[status])}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
      <div className="mt-4">
        <p className="text-sm font-bold text-slate-500 mb-1">{title}</p>
        <h2 className="text-3xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">{value}</h2>
        <p className="text-xs font-bold text-slate-400 mt-2 uppercase tracking-tighter">{desc}</p>
      </div>
    </div>
  );
}

function DataPoint({ label, value, highlight, color }: any) {
  return (
    <div className="space-y-1">
       <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{label}</p>
       <p className={cn(
         "text-sm font-black",
         highlight ? "text-slate-900 dark:text-white" : "text-slate-500",
         color === 'danger' && "text-rose-500",
         color === 'success' && "text-emerald-500"
       )}>
         {value}
       </p>
    </div>
  );
}
