import { create } from "zustand";

interface AppState {
  // Sidebar
  sidebarExpanded: boolean;
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  // Chat
  chatOpen: boolean;
  chatSessionId: string | null;
  chatContext: string | null;
  openChat: (context?: string) => void;
  closeChat: () => void;
  setChatSessionId: (id: string) => void;
  setChatContext: (context: string | null) => void;

  // Alerts
  alertCount: number;
  criticalAlertCount: number;
  setAlertCount: (count: number) => void;
  setCriticalAlertCount: (count: number) => void;

  // Sync
  lastSyncTime: Date | null;
  isSyncing: boolean;
  setLastSyncTime: (time: Date) => void;
  setIsSyncing: (syncing: boolean) => void;

  // User
  user: {
    name: string;
    email: string;
    role: string;
    avatar?: string;
  } | null;
  setUser: (user: AppState["user"]) => void;

  // Theme
  theme: "light" | "dark" | "system";
  setTheme: (theme: AppState["theme"]) => void;
}

export const useAppStore = create<AppState>()(
  (set) => ({
    // Sidebar
    sidebarExpanded: true,
    sidebarOpen: false,
    toggleSidebar: () => set((state) => ({ sidebarExpanded: !state.sidebarExpanded })),
    setSidebarOpen: (open) => set({ sidebarOpen: open }),

    // Chat
    chatOpen: false,
    chatSessionId: null,
    chatContext: null,
    openChat: (context) => set((state) => ({ 
      chatOpen: true, 
      chatContext: context || state.chatContext,
      chatSessionId: state.chatSessionId || `session_${Math.random().toString(36).substring(7)}`
    })),
    closeChat: () => set({ chatOpen: false }),
    setChatSessionId: (id) => set({ chatSessionId: id }),
    setChatContext: (context) => set({ chatContext: context }),

    // Alerts
    alertCount: 4,
    criticalAlertCount: 1,
    setAlertCount: (count) => set({ alertCount: count }),
    setCriticalAlertCount: (count) => set({ criticalAlertCount: count }),

    // Sync
    lastSyncTime: null,
    isSyncing: false,
    setLastSyncTime: (time) => set({ lastSyncTime: time }),
    setIsSyncing: (syncing) => set({ isSyncing: syncing }),

    // User - default dashboard identity
    user: {
      name: "VIREON AI",
      email: "ai@vireon.finance",
      role: "CFO",
    },
    setUser: (user) => set({ user }),

    // Theme
    theme: "light",
    setTheme: (theme) => set({ theme }),
  })
);
