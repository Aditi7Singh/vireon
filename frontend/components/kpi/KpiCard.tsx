"use client";

import { cn } from "@/lib/utils";
import { LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface KpiCardProps {
  title: string;
  value: string;
  change?: number;
  changeLabel?: string;
  icon: LucideIcon;
  status?: "healthy" | "warning" | "critical" | "neutral";
  className?: string;
}

export function KpiCard({
  title,
  value,
  change,
  changeLabel = "vs last month",
  icon: Icon,
  status = "neutral",
  className,
}: KpiCardProps) {
  const statusGradients = {
    healthy: "from-emerald-500/20 to-emerald-500/5 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
    warning: "from-amber-500/20 to-amber-500/5 text-amber-600 dark:text-amber-400 border-amber-500/20",
    critical: "from-rose-500/20 to-rose-500/5 text-rose-600 dark:text-rose-400 border-rose-500/20",
    neutral: "from-slate-500/20 to-slate-500/5 text-slate-600 dark:text-slate-400 border-slate-500/20",
  };

  const statusIcons = {
    healthy: "bg-emerald-500 text-white shadow-lg shadow-emerald-500/30",
    warning: "bg-amber-500 text-white shadow-lg shadow-amber-500/30",
    critical: "bg-rose-500 text-white shadow-lg shadow-rose-500/30",
    neutral: "bg-slate-600 text-white shadow-lg shadow-slate-500/30",
  };

  const getTrendIcon = () => {
    if (!change) return <Minus className="w-3.5 h-3.5" />;
    return change > 0 ? (
      <TrendingUp className="w-3.5 h-3.5" />
    ) : (
      <TrendingDown className="w-3.5 h-3.5" />
    );
  };

  const getTrendColor = () => {
    if (!change) return "text-slate-500";
    const isPositiveGood = !title.toLowerCase().includes("burn") && !title.toLowerCase().includes("expense");
    if (isPositiveGood) {
      return change > 0 ? "text-emerald-500" : "text-rose-500";
    }
    return change < 0 ? "text-emerald-500" : "text-rose-500";
  };

  return (
    <div
      className={cn(
        "glass-card relative overflow-hidden group p-6 rounded-2xl transition-all duration-500 hover:-translate-y-1 hover:shadow-2xl hover:shadow-indigo-500/10",
        className
      )}
    >
      {/* Background Glow */}
      <div className={cn(
        "absolute -right-4 -top-4 w-24 h-24 blur-3xl opacity-10 rounded-full transition-opacity duration-500 group-hover:opacity-20",
        status === "healthy" ? "bg-emerald-500" : status === "warning" ? "bg-amber-500" : status === "critical" ? "bg-rose-500" : "bg-indigo-500"
      )} />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-6">
          <div className={cn("p-3 rounded-xl transition-transform duration-500 group-hover:scale-110", statusIcons[status])}>
            <Icon className="w-5 h-5" />
          </div>
          {change !== undefined && (
            <div className={cn("flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-white/50 dark:bg-slate-900/50 border border-white/20 dark:border-slate-800/50 shadow-sm", getTrendColor())}>
              {getTrendIcon()}
              <span>{Math.abs(change).toFixed(1)}%</span>
            </div>
          )}
        </div>

        <p className="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-1 tracking-wide uppercase text-[10px]">
          {title}
        </p>
        
        <div className="flex items-baseline gap-2">
          <h3 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white font-outfit">
            {value}
          </h3>
          {status !== "neutral" && (
             <span className={cn("w-2 h-2 rounded-full animate-pulse", 
              status === "healthy" ? "bg-emerald-500" : 
              status === "warning" ? "bg-amber-500" : 
              "bg-rose-500"
             )} />
          )}
        </div>

        {changeLabel && (
          <p className="text-xs text-slate-400 mt-3 font-medium flex items-center gap-1.5">
            <span className="w-1 h-1 rounded-full bg-slate-300 dark:bg-slate-700" />
            {changeLabel}
          </p>
        )}
      </div>
    </div>
  );
}

export function KpiCardSkeleton() {
  return (
    <div className="glass-card p-6 rounded-2xl animate-pulse">
      <div className="flex items-start justify-between mb-6">
        <div className="w-11 h-11 bg-slate-200 dark:bg-slate-800 rounded-xl" />
        <div className="w-16 h-6 bg-slate-200 dark:bg-slate-800 rounded-full" />
      </div>
      <div className="w-24 h-4 bg-slate-200 dark:bg-slate-800 rounded mb-2" />
      <div className="w-40 h-10 bg-slate-200 dark:bg-slate-800 rounded-xl" />
    </div>
  );
}

export default KpiCard;
