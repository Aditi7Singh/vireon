"use client";

import { Search, Bell, RefreshCw, Settings, User, LogOut, ChevronDown, Upload, FileText } from "lucide-react";
import { useAppStore } from "@/lib/store";
import Link from "next/link";
import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";

export function TopBar({ title, subtitle }: { title: string; subtitle?: string }) {
  const {
    lastSyncTime,
    isSyncing,
    setIsSyncing,
    setLastSyncTime,
    alertCount,
    criticalAlertCount,
    user,
  } = useAppStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleRefresh = async () => {
    setIsSyncing(true);
    setTimeout(() => {
      setLastSyncTime(new Date());
      setIsSyncing(false);
    }, 2000);
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("auth_token");
    setUserMenuOpen(false);
    router.replace("/login");
  };

  const initials = user?.name?.split(" ").map((n: string) => n[0]).join("") || "AS";

  return (
    <header className="h-16 flex items-center justify-between px-6 bg-[#fffaf3]/90 backdrop-blur-md border-b border-[#e4d7c8] sticky top-0 z-30 transition-all duration-200">
      {/* Left: Title + Search */}
      <div className="flex items-center gap-4 flex-1 min-w-0">
        {title && (
          <div className="hidden md:flex flex-col leading-tight shrink-0">
            <h1 className="text-base font-black text-[#1f1a16] whitespace-nowrap">{title}</h1>
            {subtitle && <p className="text-[10px] text-[#8b7a69] font-medium">{subtitle}</p>}
          </div>
        )}
        <div className="relative max-w-xs w-full hidden lg:block group">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#8b7a69] group-focus-within:text-[#a15a2a]" />
          <input
            type="text"
            placeholder="Search transactions, reports... (⌘K)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white border border-[#e1d3c2] rounded-xl text-xs focus:outline-none focus:border-[#bf7a49] transition-all text-[#28231f] placeholder-[#a19283]"
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-2.5">
        {/* Data Import quick link */}
        <Link
          href="/data-import"
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-[#4d3d2a] rounded-lg border border-[#dfcfba] bg-white hover:bg-[#f9f0e0] transition"
        >
          <Upload className="w-3.5 h-3.5" />
          Import
        </Link>

        {/* Sync Button */}
        <button
          onClick={handleRefresh}
          disabled={isSyncing}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg transition-all border",
            isSyncing
              ? "bg-[#f2e9dd] text-[#9b8e82] border-[#e3d7c9] cursor-wait"
              : "bg-[#1f1a16] text-[#fff6ee] border-[#2a221c] hover:bg-[#14110f] active:scale-95"
          )}
        >
          <RefreshCw className={cn("w-3.5 h-3.5 text-[#f3ceb2]", isSyncing && "animate-spin")} />
          <span className="hidden sm:inline">{isSyncing ? "Syncing..." : "Sync"}</span>
        </button>

        {/* Notifications */}
        <Link
          href="/anomalies"
          className="relative p-2 text-[#6f6357] hover:text-[#201b17] bg-white rounded-lg border border-[#e1d4c6] transition-all hover:bg-[#fdf7ef] active:scale-95"
        >
          <Bell className="w-4.5 h-4.5" />
          {alertCount > 0 && (
            <span className={cn(
              "absolute -top-1 -right-1 flex items-center justify-center min-w-4 h-4 px-1 text-[9px] font-bold rounded-full text-white ring-2 ring-[#fffaf3]",
              criticalAlertCount > 0 ? "bg-rose-600" : "bg-[#9d5527]"
            )}>
              {alertCount}
            </span>
          )}
        </Link>

        <Link
          href="/features"
          className="hidden sm:block px-3 py-1.5 text-xs font-semibold text-[#4d3d2a] rounded-lg border border-[#dfcfba] bg-white hover:bg-[#f9f0e0] transition"
        >
          Features
        </Link>

        {/* User profile dropdown */}
        <div className="relative pl-3 border-l border-[#e5d8c9]" ref={menuRef}>
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-2 rounded-xl p-1 hover:bg-[#f5efe5] transition-colors"
          >
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#2c2520] to-[#4c3a2d] flex items-center justify-center text-[#fff7ef] font-black text-xs shadow-md">
              {initials}
            </div>
            <div className="flex-col items-end hidden sm:flex">
              <span className="text-xs font-bold text-[#1f1a16] leading-tight">
                {user?.name || "Aditi Singh"}
              </span>
              <span className="text-[9px] font-bold text-[#8d4f27] uppercase tracking-wider bg-[#f6e7d7] px-1.5 py-0.5 rounded-md">
                {user?.role || "FOUNDER"}
              </span>
            </div>
            <ChevronDown className={cn("w-3.5 h-3.5 text-[#8b7a69] transition-transform", userMenuOpen && "rotate-180")} />
          </button>

          {userMenuOpen && (
            <div className="absolute right-0 top-full mt-2 w-60 bg-white rounded-2xl border border-[#e3d6c7] shadow-2xl z-50 overflow-hidden">
              {/* User Info */}
              <div className="px-4 py-3 border-b border-[#f0e8de] bg-[#faf5ed]">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#2c2520] to-[#4c3a2d] flex items-center justify-center text-[#fff7ef] font-black text-sm shadow">
                    {initials}
                  </div>
                  <div>
                    <p className="font-bold text-sm text-[#1f1a16]">{user?.name || "Aditi Singh"}</p>
                    <p className="text-xs text-[#8b7a69]">{user?.email || "ceo@vireon.ai"}</p>
                    <span className="mt-0.5 inline-block px-2 py-0.5 rounded-md bg-[#f6e7d7] text-[#8d4f27] text-[9px] font-black uppercase tracking-wider">
                      {user?.role || "FOUNDER"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Menu Items */}
              <div className="py-1.5">
                <Link
                  href="/settings"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-[#4d3d2a] hover:bg-[#faf5ec] transition-colors"
                >
                  <Settings className="w-4 h-4 text-[#8b7a69]" />
                  Account Settings
                </Link>
                <Link
                  href="/data-import"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-[#4d3d2a] hover:bg-[#faf5ec] transition-colors"
                >
                  <Upload className="w-4 h-4 text-[#8b7a69]" />
                  Import Data
                </Link>
                <Link
                  href="/reports"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-[#4d3d2a] hover:bg-[#faf5ec] transition-colors"
                >
                  <FileText className="w-4 h-4 text-[#8b7a69]" />
                  Financial Reports
                </Link>
              </div>

              <div className="border-t border-[#f0e8de] py-1.5">
                <Link
                  href="/login"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-[#4d3d2a] hover:bg-[#faf5ec] transition-colors"
                >
                  <User className="w-4 h-4 text-[#8b7a69]" />
                  Switch Role
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default TopBar;
