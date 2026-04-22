"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import api, { CollectionsAging } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import {
  AlertTriangle, CircleDollarSign, CreditCard,
  RefreshCw, Sparkles, Users, Mail, ExternalLink, TrendingDown,
} from "lucide-react";

// Customer display names for demo overdue items (keyed by invoice_id)
const DEMO_CUSTOMERS: Record<string, string> = {
  "1": "Nexus Ventures",
  "2": "Vertex Systems",
  "3": "Skyline Retail",
};

const bucketLabels: Record<string, string> = {
  "0_30":    "Current (0–30 days)",
  "31_60":   "31–60 days",
  "61_90":   "61–90 days",
  "90_plus": "90+ days",
};

const bucketColors: Record<string, string> = {
  "0_30":    "bg-emerald-500",
  "31_60":   "bg-amber-500",
  "61_90":   "bg-orange-500",
  "90_plus": "bg-red-500",
};

// Realistic fallback shown when the API is unavailable in demo
const DEMO_DATA: CollectionsAging = {
  ar: {
    total_open: 93100,
    buckets: { "0_30": 55400, "31_60": 26500, "61_90": 7200, "90_plus": 4000 },
  },
  ap: {
    total_open: 62800,
    buckets: { "0_30": 47300, "31_60": 12000, "61_90": 3500, "90_plus": 0 },
  },
  overdue_receivables: [
    { invoice_id: "1", invoice_number: "INV-2026-043", due_date: null, days_overdue: 31,  amount_due: 7200 },
    { invoice_id: "2", invoice_number: "INV-2025-118", due_date: null, days_overdue: 67,  amount_due: 11000 },
    { invoice_id: "3", invoice_number: "INV-2025-104", due_date: null, days_overdue: 15,  amount_due: 4000 },
  ],
  as_of: "2026-04-21",
};

function urgencyColor(days: number): string {
  if (days >= 60) return "bg-red-50 border-red-200 text-red-700";
  if (days >= 30) return "bg-amber-50 border-amber-200 text-amber-700";
  return "bg-orange-50 border-orange-200 text-orange-700";
}

export default function CollectionsPage() {
  const { openChat } = useAppStore();
  const [data, setData] = useState<CollectionsAging | null>(null);
  const [loading, setLoading] = useState(true);
  const [usingDemo, setUsingDemo] = useState(false);
  const [remindedIds, setRemindedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const health = await api.getStartupHealth();
        const cid = health.default_company_id;
        if (!cid) throw new Error("no company");
        const result = await api.getCollectionsAging(cid);
        // Use demo data if API returns empty buckets
        const hasData = Object.values(result.ar?.buckets ?? {}).some((v) => v > 0);
        if (hasData) {
          setData(result);
        } else {
          setData(DEMO_DATA);
          setUsingDemo(true);
        }
      } catch {
        setData(DEMO_DATA);
        setUsingDemo(true);
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const arBuckets = data?.ar?.buckets ?? {};
  const apBuckets = data?.ap?.buckets ?? {};
  const overdue   = data?.overdue_receivables ?? [];
  const arTotal   = data?.ar?.total_open ?? 0;
  const apTotal   = data?.ap?.total_open ?? 0;
  const overdueTotal = overdue.reduce((s, i) => s + i.amount_due, 0);

  const collectionRate = arTotal > 0
    ? Math.round(((arTotal - overdueTotal) / arTotal) * 100)
    : 0;

  function sendReminder(id: string) {
    setRemindedIds((prev) => new Set([...prev, id]));
  }

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Collections" />
      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* Hero */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <CreditCard className="h-3.5 w-3.5" />
                Receivables &amp; Payables Aging
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Collections control room</h1>
              <p className="mt-2 text-sm text-[#5f5344]">
                Prioritize overdue receivables, monitor AP timing, and keep working capital disciplined.
              </p>
            </div>
            <div className="flex items-center gap-3">
              {usingDemo && (
                <span className="rounded-full bg-amber-100 border border-amber-200 px-3 py-1 text-xs font-medium text-amber-700">
                  Demo data
                </span>
              )}
              <button
                onClick={() => openChat("Review our AR aging and recommend the top 3 collection actions to take this week.")}
                className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
              >
                <Sparkles className="h-4 w-4" />
                Ask Finley
              </button>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "AR Open",      value: formatCurrency(arTotal),     icon: Users,          sub: `${overdue.length} overdue` },
            { label: "AP Open",      value: formatCurrency(apTotal),     icon: CircleDollarSign, sub: "across all vendors" },
            { label: "Overdue AR",   value: formatCurrency(overdueTotal), icon: AlertTriangle,  sub: `${overdue.length} invoices`, warn: true },
            { label: "Collection %", value: `${collectionRate}%`,        icon: TrendingDown,   sub: data?.as_of ? `As of ${data.as_of}` : "—" },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <article key={item.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{item.label}</p>
                  <Icon className={`h-4 w-4 ${item.warn ? "text-red-500" : "text-[#87602a]"}`} />
                </div>
                <p className={`mt-2 text-2xl font-semibold ${item.warn && overdueTotal > 0 ? "text-red-600" : "text-[#2a2017]"}`}>
                  {item.value}
                </p>
                <p className="mt-1 text-xs text-[#9a8872]">{item.sub}</p>
              </article>
            );
          })}
        </section>

        {/* AR + AP Aging side by side */}
        <section className="grid gap-4 lg:grid-cols-2">
          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
            <h2 className="text-base font-bold text-[#2a2017] mb-4">AR Aging</h2>
            <div className="space-y-3">
              {Object.entries(arBuckets).map(([bucket, amount]) => (
                <div key={bucket}>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-[#6f5f4b]">{bucketLabels[bucket] ?? bucket}</span>
                    <span className="font-semibold text-[#2a2017]">{formatCurrency(amount)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-[#f0ebe3] overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all ${bucketColors[bucket] ?? "bg-[#a96a14]"}`}
                      style={{ width: `${Math.min(100, arTotal > 0 ? (amount / arTotal) * 100 : 0)}%` }}
                    />
                  </div>
                </div>
              ))}
              {Object.keys(arBuckets).length === 0 && (
                <p className="text-sm text-[#9a8872]">No AR data available.</p>
              )}
            </div>
          </article>

          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
            <h2 className="text-base font-bold text-[#2a2017] mb-4">AP Aging</h2>
            <div className="space-y-3">
              {Object.entries(apBuckets).map(([bucket, amount]) => (
                <div key={bucket}>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-[#6f5f4b]">{bucketLabels[bucket] ?? bucket}</span>
                    <span className="font-semibold text-[#2a2017]">{formatCurrency(amount)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-[#f0ebe3] overflow-hidden">
                    <div
                      className="h-2 rounded-full bg-[#7d4f13] transition-all"
                      style={{ width: `${Math.min(100, apTotal > 0 ? (amount / apTotal) * 100 : 0)}%` }}
                    />
                  </div>
                </div>
              ))}
              {Object.keys(apBuckets).length === 0 && (
                <p className="text-sm text-[#9a8872]">No AP data available.</p>
              )}
            </div>
          </article>
        </section>

        {/* Overdue Receivables with action buttons */}
        <section className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] overflow-hidden">
          <div className="flex items-center justify-between p-5 border-b border-[#ede8e0]">
            <h2 className="text-base font-bold text-[#2a2017]">Overdue Receivables</h2>
            {overdue.length > 0 && (
              <button
                onClick={() => openChat(`Draft collection emails for these overdue invoices: ${overdue.map((i) => `${i.invoice_number} (${i.days_overdue} days, ${formatCurrency(i.amount_due)})`).join(", ")}`)}
                className="inline-flex items-center gap-1.5 rounded-lg bg-[#fff4dd] border border-[#d9c29a] px-3 py-1.5 text-xs font-semibold text-[#8c5c19] hover:bg-[#ffecc0]"
              >
                <Sparkles className="h-3.5 w-3.5" /> AI Draft Reminders
              </button>
            )}
          </div>
          <div className="divide-y divide-[#f0ebe3]">
            {overdue.slice(0, 8).map((item) => (
              <div key={item.invoice_id} className={`flex items-center justify-between px-5 py-4 border-l-4 ${urgencyColor(item.days_overdue ?? 0).split(" ")[0].replace("bg-", "border-")}`}>
                <div className="flex items-center gap-4">
                  <div className={`rounded-lg border px-2.5 py-1 text-xs font-bold ${urgencyColor(item.days_overdue ?? 0)}`}>
                    {item.days_overdue ?? 0}d
                  </div>
                  <div>
                    <p className="font-semibold text-[#2a2017] text-sm">
                      {DEMO_CUSTOMERS[item.invoice_id] ?? item.invoice_number}
                    </p>
                    <p className="text-xs text-[#9a8872]">{item.invoice_number} · {item.days_overdue} days overdue</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-bold text-[#9a461f]">{formatCurrency(item.amount_due)}</span>
                  {remindedIds.has(item.invoice_id) ? (
                    <span className="rounded-lg bg-emerald-50 border border-emerald-200 px-2.5 py-1 text-xs font-medium text-emerald-700">
                      Sent ✓
                    </span>
                  ) : (
                    <button
                      onClick={() => sendReminder(item.invoice_id)}
                      className="inline-flex items-center gap-1 rounded-lg border border-[#ddd2c2] bg-white px-2.5 py-1 text-xs font-medium text-[#776b5a] hover:bg-[#f5f0ea]"
                    >
                      <Mail className="h-3.5 w-3.5" /> Remind
                    </button>
                  )}
                  <button className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#9a8872]" title="View invoice">
                    <ExternalLink className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            ))}
            {overdue.length === 0 && (
              <div className="px-5 py-10 text-center text-sm text-[#9a8872]">
                No overdue receivables.
              </div>
            )}
          </div>
        </section>

        {loading && (
          <div className="flex items-center gap-2 rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-4 text-sm text-[#6f5f4b]">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading collections data...
          </div>
        )}
      </div>
    </div>
  );
}
