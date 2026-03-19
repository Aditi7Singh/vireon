"use client";

import Sidebar from "@/components/Sidebar";
import ChatDrawer from "@/components/ChatDrawer";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";

import { useEffect } from "react";
import api from "@/lib/api";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { sidebarExpanded, setUser } = useAppStore();

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

  return (
    <div className="flex h-screen bg-[#020617] overflow-hidden font-sans antialiased text-slate-200">
      {/* Sidebar */}
      <Sidebar />

      <div className="flex flex-col flex-1 min-w-0 transition-all duration-500 relative">
        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto no-scrollbar relative z-10">
          <div className="max-w-[1920px] mx-auto min-h-full">
            {children}
          </div>
        </main>

        {/* Cinematic Background Gradients */}
        <div className="absolute top-0 right-0 w-[50%] h-[50%] bg-indigo-500/5 blur-[120px] rounded-full pointer-events-none -z-0 opacity-50" />
        <div className="absolute bottom-0 left-0 w-[50%] h-[50%] bg-emerald-500/5 blur-[120px] rounded-full pointer-events-none -z-0 opacity-50" />
      </div>

      {/* Persistent AI Interface */}
      <ChatDrawer />
    </div>
  );
}
