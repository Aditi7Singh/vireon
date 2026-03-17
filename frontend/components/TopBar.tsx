"use client";

import { Search, Bell, RefreshCw, Settings, User, Command } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { formatRelativeTime } from "@/lib/utils";
import Link from "next/link";
import { useState } from "react";
import { cn } from "@/lib/utils";

export function TopBar({ title }: { title: string }) {
  const { 
    lastSyncTime, 
    isSyncing, 
    setIsSyncing, 
    setLastSyncTime,
    alertCount,
    criticalAlertCount,
    user
  } = useAppStore();
  const [searchQuery, setSearchQuery] = useState("");

  const handleRefresh = async () => {
    setIsSyncing(true);
    setTimeout(() => {
      setLastSyncTime(new Date());
      setIsSyncing(false);
    }, 2000);
  };

  return (
    <header className="h-20 flex items-center justify-between px-8 bg-white/70 dark:bg-slate-950/70 backdrop-blur-xl border-b border-slate-200/50 dark:border-slate-800/50 sticky top-0 z-30 transition-all duration-300">
      {/* Search Bar - Modern style */}
      <div className="flex items-center gap-8 flex-1">
        <div className="relative max-w-md w-full hidden lg:block group">
          <div className="absolute inset-x-0 -bottom-1 h-px bg-gradient-to-r from-transparent via-indigo-500 to-transparent opacity-0 group-focus-within:opacity-100 transition-opacity duration-500" />
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
          <input
            type="text"
            placeholder="Quick search... (⌘K)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-2.5 bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-800/50 rounded-2xl text-sm focus:outline-none focus:bg-white dark:focus:bg-slate-900 focus:ring-4 focus:ring-indigo-500/10 transition-all text-slate-900 dark:text-white placeholder-slate-500 font-medium"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 px-2 py-1 rounded bg-slate-200/50 dark:bg-slate-800/50 border border-slate-300/50 dark:border-slate-700/50">
            <Command className="w-3 h-3 text-slate-500" />
            <span className="text-[10px] font-bold text-slate-500">K</span>
          </div>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-4">
        {/* Connection Status */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-900 border border-slate-200/50 dark:border-slate-800/50">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Systems Nominal</span>
        </div>

        {/* Sync Button */}
        <button
          onClick={handleRefresh}
          disabled={isSyncing}
          className={cn(
            "flex items-center gap-2 px-4 py-2 text-sm font-bold rounded-2xl transition-all duration-300 border",
            isSyncing 
              ? "bg-slate-100 dark:bg-slate-900 text-slate-400 border-slate-200 dark:border-slate-800" 
              : "bg-white dark:bg-slate-950 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-800 hover:border-indigo-500/50 hover:bg-slate-50 dark:hover:bg-slate-900 shadow-sm"
          )}
        >
          <RefreshCw className={cn("w-3.5 h-3.5 transition-transform duration-1000", isSyncing && "animate-spin")} />
          <span className="hidden sm:inline">
            {isSyncing ? "Updating..." : lastSyncTime ? formatRelativeTime(lastSyncTime) : "Sync"}
          </span>
        </button>

        {/* Notifications */}
        <Link
          href="/anomalies"
          className="relative p-2.5 text-slate-500 hover:text-indigo-500 bg-slate-100/50 dark:bg-slate-900/50 rounded-2xl border border-slate-200/50 dark:border-slate-800/50 transition-all hover:scale-110 active:scale-95"
        >
          <Bell className="w-5 h-5" />
          {alertCount > 0 && (
            <span className={cn(
              "absolute -top-1 -right-1 flex items-center justify-center min-w-5 h-5 px-1.5 text-[10px] font-black rounded-full text-white ring-4 ring-white dark:ring-slate-950",
              criticalAlertCount > 0 ? "bg-rose-500 animate-bounce" : "bg-amber-500"
            )}>
              {alertCount}
            </span>
          )}
        </Link>

        {/* User Menu */}
        <div className="flex items-center gap-3 pl-4 border-l border-slate-200 dark:border-slate-800 ml-2">
           <div className="flex flex-col items-end hidden sm:flex">
              <span className="text-xs font-bold text-slate-900 dark:text-white font-outfit leading-none">
                {user?.name || "Aditi Singh"}
              </span>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="text-[9px] font-black text-indigo-500 uppercase tracking-widest bg-indigo-500/10 px-1.5 py-0.5 rounded-md">
                   {user?.role || "ADMIN"}
                </span>
                <span className="text-[9px] text-slate-400 font-medium uppercase tracking-tighter">
                  Enterprise Plan
                </span>
              </div>
           </div>
           <button className="relative group">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-500 p-0.5 shadow-lg group-hover:scale-110 transition-transform duration-300">
                <div className="w-full h-full rounded-[14px] bg-slate-950 flex items-center justify-center text-white font-black text-xs uppercase">
                   {user?.name?.split(' ').map(n => n[0]).join('') || "AD"}
                </div>
              </div>
           </button>
        </div>
      </div>
    </header>
  );
}

export default TopBar;
