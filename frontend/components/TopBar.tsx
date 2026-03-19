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
    <header className="h-20 flex items-center justify-between px-8 bg-slate-950/80 backdrop-blur-md border-b border-white/5 sticky top-0 z-30 transition-all duration-200">
      {/* Search Bar - Professional */}
      <div className="flex items-center gap-6 flex-1">
        <div className="relative max-w-sm w-full hidden lg:block group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-indigo-400" />
          <input
            type="text"
            placeholder="Search financial records... (⌘K)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-2.5 bg-slate-900 border border-white/10 rounded-xl text-sm focus:outline-none focus:border-indigo-500/50 transition-all text-white placeholder-slate-500"
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-4">
        {/* Sync Button */}
        <button
          onClick={handleRefresh}
          disabled={isSyncing}
          className={cn(
            "flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-lg transition-all border",
            isSyncing
              ? "bg-slate-800 text-slate-500 border-white/5 cursor-wait"
              : "bg-slate-800 text-white border-white/10 hover:border-indigo-500/50 hover:bg-slate-700 active:scale-95"
          )}
        >
          <RefreshCw className={cn("w-3.5 h-3.5 text-indigo-400", isSyncing && "animate-spin")} />
          <span>{isSyncing ? "Syncing..." : "Refresh Data"}</span>
        </button>

        {/* Notifications */}
        <Link
          href="/anomalies"
          className="relative p-2.5 text-slate-400 hover:text-white bg-slate-800 rounded-lg border border-white/10 transition-all hover:bg-slate-700 active:scale-95"
        >
          <Bell className="w-5 h-5" />
          {alertCount > 0 && (
            <span className={cn(
              "absolute -top-1 -right-1 flex items-center justify-center min-w-5 h-5 px-1 text-[10px] font-bold rounded-full text-white ring-2 ring-slate-950",
              criticalAlertCount > 0 ? "bg-rose-600" : "bg-indigo-600"
            )}>
              {alertCount}
            </span>
          )}
        </Link>

        {/* User profile */}
        <div className="flex items-center gap-3 pl-4 border-l border-white/5 ml-2">
          <div className="flex flex-col items-end hidden sm:flex">
            <span className="text-sm font-bold text-white">
              {user?.name || "Aditi Singh"}
            </span>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              {user?.role || "FOUNDER"}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default TopBar;
