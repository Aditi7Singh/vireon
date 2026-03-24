"use client";

import { useEffect, useMemo, useState } from "react";
import TopBar from "@/components/TopBar";
import { useAlerts } from "@/hooks/useFinancialData";
import { useAppStore } from "@/lib/store";
import api from "@/lib/api";
import { cn, formatCurrency, formatRelativeTime } from "@/lib/utils";
import { Alert } from "@/lib/api";
import { AlertTriangle, CheckCircle2, RefreshCw, Search, ShieldCheck, Sparkles } from "lucide-react";

export default function AnomaliesPage() {
  const { alerts, isLoading, mutate } = useAlerts();
  const { openChat, isSyncing, setIsSyncing, setAlertCount, setCriticalAlertCount } = useAppStore();
  const [filter, setFilter] = useState<"all" | "critical" | "warning" | "info">("all");
  const [query, setQuery] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    setAlertCount(alerts?.total ?? 0);
    setCriticalAlertCount(alerts?.critical_count ?? 0);
  }, [alerts, setAlertCount, setCriticalAlertCount]);

  const filteredAlerts: Alert[] = useMemo(() => {
    const base = alerts?.alerts ?? [];
    return base.filter((alert: Alert) => {
      const matchesSeverity = filter === "all" || alert.severity === filter;
      const normalized = `${alert.description} ${alert.alert_type} ${alert.category}`.toLowerCase();
      const matchesQuery = !query.trim() || normalized.includes(query.trim().toLowerCase());
      return matchesSeverity && matchesQuery;
    });
  }, [alerts, filter, query]);

  const handleScan = async () => {
    setActionError(null);
    setIsSyncing(true);
    try {
      await api.triggerScan();
      await mutate();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Failed to trigger anomaly scan.");
    } finally {
      setIsSyncing(false);
    }
  };

  const handleDismiss = async (alertId: string) => {
    setActionError(null);
    try {
      await api.dismissAlert(alertId);
      await mutate();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Failed to dismiss alert.");
    }
  };

  const handleSeedDemo = async () => {
    setActionError(null);
    try {
      await api.seedDemoAlerts();
      await mutate();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Failed to seed demo anomalies.");
    }
  };

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Anomaly Detection" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#c8ddca] bg-[#eaf7ed] px-3 py-1 text-xs font-semibold text-[#2f6a45]">
                <ShieldCheck className="h-3.5 w-3.5" />
                Sentinel active
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Audit and Compliance Alerts</h1>
              <p className="mt-2 text-sm text-[#5f5344]">Identify unusual spikes before they affect runway.</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleSeedDemo}
                className="inline-flex items-center gap-2 rounded-xl border border-[#d4c2a5] bg-[#fff3df] px-4 py-2.5 text-sm font-medium text-[#6a4d26] hover:bg-[#f6e5c8]"
              >
                Seed demo alerts
              </button>
              <button onClick={handleScan} className="inline-flex items-center gap-2 rounded-xl border border-[#ccb89a] bg-[#fff9ee] px-4 py-2.5 text-sm font-medium text-[#5f4828] hover:bg-[#f8ebd7]" disabled={isSyncing}>
                <RefreshCw className={cn("h-4 w-4", isSyncing && "animate-spin")} />
                {isSyncing ? "Scanning" : "Run scan"}
              </button>
              <button onClick={() => openChat("Deep Forensic Analysis Request")} className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                <Sparkles className="h-4 w-4" />
                Ask AI
              </button>
            </div>
          </div>
        </section>

        <section className="flex flex-wrap items-center gap-2">
          {actionError && (
            <p className="w-full rounded-xl border border-[#ebc1b8] bg-[#fff2ef] px-3 py-2 text-xs text-[#9f3f30]">{actionError}</p>
          )}
          {(["all", "critical", "warning", "info"] as const).map((f) => (
            <button key={f} onClick={() => setFilter(f)} className={cn("rounded-full border px-3 py-1.5 text-xs font-medium", filter === f ? "border-[#b99561] bg-[#f5e7cf] text-[#6b4a1e]" : "border-[#dbcdb9] bg-[#fffdf8] text-[#7a6a57]")}>
              {f}
            </button>
          ))}
          <div className="relative ml-auto w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8a7b68]" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full rounded-xl border border-[#dbcdb9] bg-[#fffdf8] py-2 pl-10 pr-3 text-sm"
              placeholder="Search alerts"
            />
          </div>
        </section>

        <section className="space-y-4">
          {filteredAlerts.map((alert: Alert) => (
            <article key={alert.id} className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
              <div className="flex flex-wrap items-center gap-2 text-xs text-[#7e715f]">
                <span className={cn("rounded-full px-2.5 py-1", alert.severity === "critical" ? "bg-[#f8d8cc] text-[#9b3a1f]" : alert.severity === "warning" ? "bg-[#f9ecd2] text-[#7a4f14]" : "bg-[#e3efe9] text-[#2f6a45]")}>{alert.severity}</span>
                <span>{alert.alert_type}</span>
                <span>{formatRelativeTime(alert.created_at)}</span>
              </div>
              <h3 className="mt-2 text-lg font-semibold text-[#2a2017]">{alert.description}</h3>
              <div className="mt-3 grid gap-3 sm:grid-cols-4 text-sm text-[#5f5243]">
                <p>Exposure: {formatCurrency(alert.amount)}</p>
                <p>Baseline: {formatCurrency(alert.baseline)}</p>
                <p>Delta: {alert.delta_pct.toFixed(1)}%</p>
                <p>Runway impact: -{alert.runway_impact.toFixed(1)} mo</p>
              </div>
              <div className="mt-4 flex items-center gap-2">
                <button
                  onClick={() => openChat(`Anomaly Analysis: ${alert.description}`)}
                  className="rounded-lg border border-[#cbb48f] bg-[#fbf2e2] px-3 py-1.5 text-xs font-semibold text-[#6c512f] hover:bg-[#f2e2c9]"
                >
                  Analyze with AI
                </button>
                <button
                  onClick={() => handleDismiss(alert.id)}
                  className="rounded-lg border border-[#d6c7b1] bg-white px-3 py-1.5 text-xs font-semibold text-[#645643] hover:bg-[#f7f3eb]"
                >
                  Dismiss
                </button>
              </div>
            </article>
          ))}

          {filteredAlerts.length === 0 && !isLoading && (
            <article className="rounded-2xl border border-dashed border-[#d9cdbc] bg-[#fffdf8] p-10 text-center">
              <CheckCircle2 className="mx-auto h-10 w-10 text-[#2f6a45]" />
              <h3 className="mt-3 text-lg font-semibold text-[#2a2017]">No active alerts</h3>
              <p className="mt-1 text-sm text-[#6f6252]">Current ledger looks healthy.</p>
            </article>
          )}
        </section>
      </div>
    </div>
  );
}
