"use client";

import { useState, useEffect } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import {
  RefreshCw, CheckCircle2, AlertTriangle, Wifi, WifiOff,
  Zap, Clock, Database, ArrowLeftRight, Activity,
  FileText, Users, Bell, Play,
} from "lucide-react";

interface SyncEvent {
  id: string;
  type: string;
  timestamp: string;
  status: "success" | "error" | "syncing";
  records?: number;
  duration_ms?: number;
  entity?: string;
}

const INITIAL_EVENTS: SyncEvent[] = [
  { id: "1", type: "sync_complete", timestamp: "2026-04-28T10:45:00Z", status: "success", records: 34, duration_ms: 412 },
  { id: "2", type: "record_updated", timestamp: "2026-04-28T10:44:30Z", status: "success", entity: "Sales Invoice INV-2026-089" },
  { id: "3", type: "record_created", timestamp: "2026-04-28T10:42:15Z", status: "success", entity: "Customer: Acme Corp" },
  { id: "4", type: "sync_complete", timestamp: "2026-04-28T10:30:00Z", status: "success", records: 27, duration_ms: 388 },
  { id: "5", type: "sync_error", timestamp: "2026-04-28T09:15:00Z", status: "error", entity: "ERPNext connection timeout" },
  { id: "6", type: "sync_complete", timestamp: "2026-04-28T09:00:00Z", status: "success", records: 41, duration_ms: 527 },
];

const ENTITY_STATS = [
  { label: "Invoices", synced: 1247, pending: 3, icon: FileText, color: "text-blue-600" },
  { label: "Contacts", synced: 384, pending: 1, icon: Users, color: "text-violet-600" },
  { label: "Payments", synced: 892, pending: 0, icon: ArrowLeftRight, color: "text-emerald-600" },
];

function typeLabel(type: string): string {
  return {
    sync_complete: "Sync Complete",
    sync_error: "Sync Error",
    record_created: "Record Created",
    record_updated: "Record Updated",
    heartbeat: "Heartbeat",
  }[type] || type;
}

export default function RealtimeSyncPage() {
  const { openChat } = useAppStore();
  const [events, setEvents] = useState<SyncEvent[]>(INITIAL_EVENTS);
  const [connected, setConnected] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [pulseCount, setPulseCount] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPulseCount(c => c + 1);
      if (Math.random() > 0.6) {
        const newEvent: SyncEvent = {
          id: Date.now().toString(),
          type: Math.random() > 0.3 ? "heartbeat" : Math.random() > 0.5 ? "record_updated" : "sync_complete",
          timestamp: new Date().toISOString(),
          status: Math.random() > 0.1 ? "success" : "error",
          records: Math.floor(Math.random() * 20) + 1,
          duration_ms: Math.floor(Math.random() * 300) + 200,
        };
        setEvents(prev => [newEvent, ...prev.slice(0, 49)]);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSync = () => {
    setSyncing(true);
    const syncEvent: SyncEvent = {
      id: Date.now().toString(),
      type: "sync_complete",
      timestamp: new Date().toISOString(),
      status: "success",
      records: Math.floor(Math.random() * 40) + 10,
      duration_ms: Math.floor(Math.random() * 400) + 200,
    };
    setTimeout(() => {
      setSyncing(false);
      setEvents(prev => [syncEvent, ...prev]);
    }, 2000);
  };

  const successCount = events.filter(e => e.status === "success").length;
  const errorCount = events.filter(e => e.status === "error").length;
  const lastSync = events.find(e => e.type === "sync_complete");

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Real-Time ERP Sync" />
      <div className="max-w-5xl mx-auto px-6 pt-6 space-y-6">

        {/* Connection Status Banner */}
        <div className={cn(
          "flex items-center gap-3 p-4 rounded-2xl border",
          connected ? "bg-emerald-50 border-emerald-200" : "bg-red-50 border-red-200"
        )}>
          {connected
            ? <Wifi className="w-5 h-5 text-emerald-600 shrink-0" />
            : <WifiOff className="w-5 h-5 text-red-600 shrink-0" />}
          <div className="flex-1">
            <div className={cn("font-bold text-sm", connected ? "text-emerald-800" : "text-red-800")}>
              {connected ? "Live Sync Active — ERPNext Connected" : "Sync Disconnected — Check ERPNext credentials"}
            </div>
            <div className="text-xs text-[#6a6054] mt-0.5">
              {connected
                ? `Last sync: ${lastSync ? new Date(lastSync.timestamp).toLocaleTimeString() : "—"} · Mode: Webhook + SSE stream`
                : "Configure ERPNEXT_URL, ERPNEXT_API_KEY, and ERPNEXT_API_SECRET in environment."}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className={cn("w-2 h-2 rounded-full animate-pulse", connected ? "bg-emerald-500" : "bg-red-500")} />
            <span className="text-xs font-semibold text-[#6a6054]">SSE Stream</span>
          </div>
        </div>

        {/* KPI Row */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Events (Last 50)", value: events.length, icon: Activity, color: "text-violet-600" },
            { label: "Successful", value: successCount, icon: CheckCircle2, color: "text-emerald-600" },
            { label: "Errors", value: errorCount, icon: AlertTriangle, color: errorCount > 0 ? "text-red-600" : "text-gray-400" },
            { label: "Avg Latency", value: `${Math.round(events.filter(e => e.duration_ms).reduce((s, e) => s + (e.duration_ms || 0), 0) / Math.max(1, events.filter(e => e.duration_ms).length))}ms`, icon: Zap, color: "text-amber-600" },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="bg-white border border-[#e8ddd4] rounded-2xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-[#8a7e74] uppercase tracking-wide">{label}</span>
                <Icon className={cn("w-4 h-4", color)} />
              </div>
              <div className={cn("text-2xl font-black", errorCount > 0 && label === "Errors" ? "text-red-600" : "text-[#1d1b17]")}>{value}</div>
            </div>
          ))}
        </div>

        {/* Entity Sync Stats */}
        <div className="grid grid-cols-3 gap-4">
          {ENTITY_STATS.map(({ label, synced, pending, icon: Icon, color }) => (
            <div key={label} className="bg-white border border-[#e8ddd4] rounded-2xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Icon className={cn("w-4 h-4", color)} />
                <span className="font-semibold text-sm text-[#1d1b17]">{label}</span>
              </div>
              <div className="flex items-end justify-between">
                <div>
                  <div className="text-xl font-black text-[#1d1b17]">{synced.toLocaleString()}</div>
                  <div className="text-xs text-[#8a7e74]">synced records</div>
                </div>
                {pending > 0 ? (
                  <div className="text-right">
                    <div className="text-sm font-black text-amber-600">{pending}</div>
                    <div className="text-[10px] text-amber-500">pending</div>
                  </div>
                ) : (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2 bg-[#b3622d] hover:bg-[#9d4f22] text-white rounded-xl text-sm font-semibold transition-all disabled:opacity-60"
          >
            <RefreshCw className={cn("w-4 h-4", syncing && "animate-spin")} />
            {syncing ? "Syncing..." : "Trigger Immediate Sync"}
          </button>
          <button
            onClick={() => openChat("Show me the current ERP sync status and any recent errors.")}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-[#e8ddd4] hover:border-[#b3622d] text-[#1d1b17] rounded-xl text-sm font-semibold transition-all"
          >
            <Bell className="w-4 h-4" /> Configure Webhooks
          </button>
        </div>

        {/* Live Event Log */}
        <div className="bg-white border border-[#e8ddd4] rounded-2xl p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-sm flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#b3622d]" />
              Live Event Stream
            </h3>
            <div className="flex items-center gap-1.5 text-xs text-emerald-600 font-semibold">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Live
            </div>
          </div>

          <div className="space-y-1.5 max-h-96 overflow-y-auto">
            {events.map(ev => (
              <div key={ev.id} className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-xl border text-xs",
                ev.status === "error" ? "bg-red-50 border-red-200" :
                ev.type === "heartbeat" ? "bg-[#f6f3ee] border-[#e8ddd4]" :
                "bg-emerald-50/50 border-emerald-100"
              )}>
                {ev.status === "error"
                  ? <AlertTriangle className="w-3.5 h-3.5 text-red-500 shrink-0" />
                  : ev.type === "heartbeat"
                  ? <div className="w-2 h-2 rounded-full bg-[#b0a499] shrink-0" />
                  : <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />}
                <span className="font-semibold text-[#1d1b17] min-w-[100px]">{typeLabel(ev.type)}</span>
                {ev.entity && <span className="text-[#6a6054] truncate flex-1">{ev.entity}</span>}
                {ev.records && <span className="text-[#6a6054]">{ev.records} records</span>}
                {ev.duration_ms && <span className="text-[#8a7e74]">{ev.duration_ms}ms</span>}
                <span className="text-[#b0a499] ml-auto shrink-0">{new Date(ev.timestamp).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Sync Architecture */}
        <div className="bg-white border border-[#e8ddd4] rounded-2xl p-5">
          <h3 className="font-bold text-sm mb-4">Sync Architecture</h3>
          <div className="flex items-center justify-between gap-2 text-center">
            {[
              { label: "ERPNext", sublabel: "Source of Truth", icon: Database, color: "bg-blue-100 text-blue-700" },
              { label: "Webhook / SSE", sublabel: "Real-time transport", icon: Zap, color: "bg-amber-100 text-amber-700" },
              { label: "Vireon DB", sublabel: "Operational store", icon: Database, color: "bg-violet-100 text-violet-700" },
              { label: "API / UI", sublabel: "Consumption layer", icon: Activity, color: "bg-emerald-100 text-emerald-700" },
            ].map(({ label, sublabel, icon: Icon, color }, i) => (
              <div key={label} className="flex items-center gap-2">
                <div className="flex-1">
                  <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mx-auto mb-1", color)}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="text-xs font-bold text-[#1d1b17]">{label}</div>
                  <div className="text-[10px] text-[#8a7e74]">{sublabel}</div>
                </div>
                {i < 3 && <div className="text-[#d8c9be] font-bold text-lg shrink-0">→</div>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
