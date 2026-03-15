/**
 * Zustand Global State Store
 * Manages: alerts, chat history, active page, UI state
 */

import { create } from 'zustand';
import { Alert, ChatMessage } from './api';

export interface AppState {
  // Sidebar & Layout
  sidebarExpanded: boolean;
  toggleSidebar: () => void;

  // Chat
  chatOpen: boolean;
  openChat: () => void;
  closeChat: () => void;
  sessionId: string;
  chatMessages: ChatMessage[];
  chatLoading: boolean;
  addChatMessage: (message: ChatMessage) => void;
  setChatMessages: (messages: ChatMessage[]) => void;
  setChatLoading: (loading: boolean) => void;
  initSession: (sessionId: string) => void;
  startNewConversation: () => void;

  // Alerts
  alerts: Alert[];
  alertCount: number;
  criticalCount: number;
  warningCount: number;
  infoCount: number;
  setAlerts: (alerts: Alert[]) => void;
  setAlertCount: (n: number) => void;

  // Sync
  lastSyncTime: Date | null;
  setLastSyncTime: (t: Date) => void;

  // Active Page
  activePage: 'dashboard' | 'runway' | 'expenses' | 'revenue' | 'alerts';
  setActivePage: (page: AppState['activePage']) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Sidebar
  sidebarExpanded: false,
  toggleSidebar: () => set((state) => ({ sidebarExpanded: !state.sidebarExpanded })),

  // Chat
  chatOpen: false,
  openChat: () => set({ chatOpen: true }),
  closeChat: () => set({ chatOpen: false }),
  sessionId: '',
  chatMessages: [],
  chatLoading: false,
  addChatMessage: (message) =>
    set((state) => ({
      chatMessages: [...state.chatMessages, message],
    })),
  setChatMessages: (messages) => set({ chatMessages: messages }),
  setChatLoading: (loading) => set({ chatLoading: loading }),
  initSession: (sessionId) => set({ sessionId, chatMessages: [] }),
  startNewConversation: () => set({ sessionId: '', chatMessages: [] }),

  // Alerts
  alerts: [],
  alertCount: 0,
  criticalCount: 0,
  warningCount: 0,
  infoCount: 0,
  setAlerts: (alerts) =>
    set({
      alerts,
      alertCount: alerts.length,
      criticalCount: alerts.filter((a) => a.severity === 'CRITICAL').length,
      warningCount: alerts.filter((a) => a.severity === 'WARNING').length,
      infoCount: alerts.filter((a) => a.severity === 'INFO').length,
    }),
  setAlertCount: (n) => set({ alertCount: n }),

  // Sync
  lastSyncTime: null,
  setLastSyncTime: (t) => set({ lastSyncTime: t }),

  // Active page
  activePage: 'dashboard',
  setActivePage: (page) => set({ activePage: page }),
}));

/**
 * Scoped hooks to prevent unnecessary re-renders
 */
export const useAlerts = () => {
  const store = useAppStore();
  return {
    alerts: store.alerts,
    alertCount: store.alertCount,
    criticalCount: store.criticalCount,
    warningCount: store.warningCount,
    infoCount: store.infoCount,
    setAlerts: store.setAlerts,
  };
};
