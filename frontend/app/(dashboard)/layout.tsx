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
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden font-inter antialiased">
      {/* Sidebar - Fixed width handled by component */}
      <Sidebar />
      
      <div className="flex flex-col flex-1 min-w-0 transition-all duration-500 relative">
        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto no-scrollbar bg-slate-50/50 dark:bg-slate-950/50">
           <div className="relative">
             {children}
           </div>
        </main>

        {/* Floating AI Background Element (Subtle) */}
        <div className="absolute -bottom-48 -right-48 w-96 h-96 bg-indigo-500/5 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute -top-48 -left-48 w-96 h-96 bg-purple-500/5 blur-[120px] rounded-full pointer-events-none" />
      </div>

      {/* Persistent AI Interface */}
      <ChatDrawer />
    </div>
  );
}
