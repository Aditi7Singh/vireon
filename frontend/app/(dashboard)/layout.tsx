"use client";

import Sidebar from "@/components/Sidebar";
import ChatDrawer from "@/components/ChatDrawer";
import { useAppStore } from "@/lib/store";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { setUser, setAlertCount, setCriticalAlertCount } = useAppStore();
  const router = useRouter();
  const [startupIssues, setStartupIssues] = useState<string[]>([]);
  const [startupActions, setStartupActions] = useState<string[]>([]);
  const [actionBusy, setActionBusy] = useState<string | null>(null);

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem("access_token") || localStorage.getItem("auth_token");
      if (!token) {
        router.replace("/login");
        return;
      }

      try {
        const user = await api.getMe();
        if (user) {
          const isDemoUser = user.username === "vireon_demo";

          const roleNorm = (user.role || "").toUpperCase();
          const displayName =
            isDemoUser              ? "Finley"       :
            user.email === "outlandishaditi11@gmail.com" ? "Aditi Singh" :
            user.email === "finley@vireon.ai"            ? "Finley"      :
            user.username;

          setUser({
            name:  displayName,
            email: isDemoUser ? "finley@vireon.ai" : (user.email || `${user.username}@vireon.ai`),
            role:  isDemoUser ? "CFO" : roleNorm,
          });

          // Role-based first-visit routing (only redirect if at bare /dashboard)
          if (window.location.pathname === "/dashboard") {
            if (roleNorm === "CEO") {
              router.replace("/dashboard/ceo");
            } else if (roleNorm === "CFO" || isDemoUser) {
              router.replace("/dashboard/finance");
            }
            // ADMIN stays on /dashboard
          }
        }
      } catch (error) {
        console.error("Failed to fetch user profile:", error);
        localStorage.removeItem("access_token");
        localStorage.removeItem("auth_token");
        router.replace("/login");
      }
    };
    fetchUser();
  }, [setUser, router]);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const health = await api.getStartupHealth();
        setStartupIssues(health.issues || []);
        setStartupActions(health.actions || []);
      } catch {
        setStartupIssues(["Startup health check unavailable"]);
        setStartupActions([]);
      }
    };
    fetchHealth();
  }, []);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const payload = await api.getAlerts();
        setAlertCount(payload.total || 0);
        setCriticalAlertCount(payload.critical_count || 0);
      } catch {
        setAlertCount(0);
        setCriticalAlertCount(0);
      }
    };
    fetchAlerts();
  }, [setAlertCount, setCriticalAlertCount]);

  const runAction = async (action: string) => {
    try {
      setActionBusy(action);
      await api.runStartupRemediation(action);
      const health = await api.getStartupHealth();
      setStartupIssues(health.issues || []);
      setStartupActions(health.actions || []);
    } catch (error) {
      console.error("Startup remediation failed:", error);
    } finally {
      setActionBusy(null);
    }
  };

  return (
    <div className="flex h-screen bg-[#f6f3ee] overflow-hidden font-sans antialiased text-[#1d1b19]">
      {/* Sidebar */}
      <Sidebar />

      <div className="flex flex-col flex-1 min-w-0 transition-all duration-500 relative">
        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto no-scrollbar relative z-10">
          <div className="max-w-[1920px] mx-auto min-h-full">
            {startupIssues.length > 0 && (
              <div className="mx-6 mt-6 rounded-2xl border border-[#e5c3a4] bg-[#fff2e7] px-4 py-3 text-[#6b3f20]">
                <p className="text-xs font-black uppercase tracking-[0.16em]">Startup Checks</p>
                <p className="mt-1 text-sm">Some data sources still need setup: {startupIssues.join(", ")}</p>
                {startupActions.length > 0 && (
                  <div className="mt-2 space-y-1 text-xs">
                    {startupActions.map((action, index) => (
                      <div key={`${action}-${index}`} className="flex items-center justify-between gap-3 rounded-lg border border-[#e8c9af] bg-white/70 px-3 py-2">
                        <p className="text-[#7a4b26]">Action: {action}</p>
                        <button
                          disabled={actionBusy === action}
                          onClick={() => runAction(action)}
                          className="rounded bg-[#9a5d34] px-2 py-1 text-[11px] font-semibold text-white disabled:opacity-60"
                        >
                          {actionBusy === action ? "Running..." : "Run"}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            {children}
          </div>
        </main>

        {/* Ambient Background Gradients */}
        <div className="absolute top-0 right-0 w-[50%] h-[50%] bg-[#f8caa8]/25 blur-[120px] rounded-full pointer-events-none -z-0 opacity-70" />
        <div className="absolute bottom-0 left-0 w-[50%] h-[50%] bg-[#f0d9bc]/25 blur-[120px] rounded-full pointer-events-none -z-0 opacity-70" />
      </div>

      {/* Persistent AI Interface */}
      <ChatDrawer />
    </div>
  );
}
