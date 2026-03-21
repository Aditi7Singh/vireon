"use client";

import Sidebar from "@/components/Sidebar";
import ChatDrawer from "@/components/ChatDrawer";
import { useAppStore } from "@/lib/store";

import { useEffect, useState } from "react";
import api from "@/lib/api";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { sidebarExpanded, setUser } = useAppStore();
  const [startupIssues, setStartupIssues] = useState<string[]>([]);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const user = await api.getMe();
        if (user) {
          // Map backend User model to frontend store user format
          setUser({
            name: user.username, // Using username as name for now
            email: user.email || `${user.username}@vireon.ai`,
            role: user.role
          });
        }
      } catch (error) {
        console.error("Failed to fetch user profile:", error);
      }
    };
    fetchUser();
  }, [setUser]);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const health = await api.getStartupHealth();
        setStartupIssues(health.issues || []);
      } catch {
        setStartupIssues(["Startup health check unavailable"]);
      }
    };
    fetchHealth();
  }, []);

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
