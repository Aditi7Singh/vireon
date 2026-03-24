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
    <header className="h-20 flex items-center justify-between px-8 bg-[#fffaf3]/85 backdrop-blur-md border-b border-[#e4d7c8] sticky top-0 z-30 transition-all duration-200">
      {/* Search Bar - Professional */}
      <div className="flex items-center gap-6 flex-1">
        <div className="relative max-w-sm w-full hidden lg:block group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8b7a69] group-focus-within:text-[#a15a2a]" />
          <input
            type="text"
            placeholder="Search financial records... (⌘K)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-2.5 bg-white border border-[#e1d3c2] rounded-xl text-sm focus:outline-none focus:border-[#bf7a49] transition-all text-[#28231f] placeholder-[#a19283]"
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
              ? "bg-[#f2e9dd] text-[#9b8e82] border-[#e3d7c9] cursor-wait"
              : "bg-[#1f1a16] text-[#fff6ee] border-[#2a221c] hover:bg-[#14110f] active:scale-95"
          )}
        >
          <RefreshCw className={cn("w-3.5 h-3.5 text-[#f3ceb2]", isSyncing && "animate-spin")} />
          <span>{isSyncing ? "Syncing..." : "Refresh Data"}</span>
        </button>

        {/* Notifications */}
        <Link
          href="/anomalies"
          className="relative p-2.5 text-[#6f6357] hover:text-[#201b17] bg-white rounded-lg border border-[#e1d4c6] transition-all hover:bg-[#fdf7ef] active:scale-95"
        >
          <Bell className="w-5 h-5" />
          {alertCount > 0 && (
            <span className={cn(
              "absolute -top-1 -right-1 flex items-center justify-center min-w-5 h-5 px-1 text-[10px] font-bold rounded-full text-white ring-2 ring-[#fffaf3]",
              criticalAlertCount > 0 ? "bg-rose-600" : "bg-[#9d5527]"
            )}>
              {alertCount}
            </span>
          )}
        </Link>

        <Link
          href="/features"
          className="px-3 py-2 text-xs font-semibold text-[#4d3d2a] rounded-lg border border-[#dfcfba] bg-white hover:bg-[#f9f0e0] transition"
        >
          Feature Hub
        </Link>

        {/* User profile */}
        <div className="flex items-center gap-3 pl-4 border-l border-[#e5d8c9] ml-2">
          <div className="flex flex-col items-end hidden sm:flex">
            <span className="text-sm font-bold text-[#1f1a16]">
              {user?.name || "Aditi Singh"}
            </span>
            <span className="text-[10px] font-bold text-[#7f7469] uppercase tracking-wider">
              {user?.role || "FOUNDER"}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default TopBar;
