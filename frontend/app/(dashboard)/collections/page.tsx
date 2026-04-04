"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import api, { CollectionsAging } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import { AlertTriangle, CircleDollarSign, Clock3, CreditCard, RefreshCw, Sparkles, Users } from "lucide-react";

const bucketLabels: Record<string, string> = {
  "0_30": "0-30 days",
  "31_60": "31-60 days",
  "61_90": "61-90 days",
  "90_plus": "90+ days",
};

export default function CollectionsPage() {
  const { openChat } = useAppStore();
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [data, setData] = useState<CollectionsAging | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const health = await api.getStartupHealth();
        const resolvedCompanyId = health.default_company_id || null;
        setCompanyId(resolvedCompanyId);
        if (!resolvedCompanyId) {
          setError("No default company is configured yet.");
          return;
        }
        setData(await api.getCollectionsAging(resolvedCompanyId));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load collections data.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const arBuckets = data?.ar?.buckets || {};
  const apBuckets = data?.ap?.buckets || {};

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Collections" />
      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <CreditCard className="h-3.5 w-3.5" />
                Receivables and payables aging
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Collections control room</h1>
              <p className="mt-2 text-sm text-[#5f5344]">Prioritize overdue receivables, monitor AP timing, and keep working capital disciplined.</p>
            </div>
            <button
              onClick={() => openChat("Review our collections aging and recommend the top AR and AP actions.")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
            >
              <Sparkles className="h-4 w-4" />
              Ask Finley
            </button>
          </div>
        </section>

        {error && <div className="rounded-2xl border border-[#ebc1b8] bg-[#fff1ee] px-4 py-3 text-sm text-[#9f3f30]">{error}</div>}

        <section className="grid gap-4 md:grid-cols-4">
          {[
            { label: "AR open", value: formatCurrency(data?.ar?.total_open || 0), icon: Users },
            { label: "AP open", value: formatCurrency(data?.ap?.total_open || 0), icon: CircleDollarSign },
            { label: "Overdue AR", value: formatCurrency(data?.overdue_receivables?.reduce((sum, item) => sum + item.amount_due, 0) || 0), icon: AlertTriangle },
            { label: "As of", value: data?.as_of || "—", icon: Clock3 },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <article key={item.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{item.label}</p>
                  <Icon className="h-4 w-4 text-[#87602a]" />
                </div>
                <p className="mt-2 text-2xl font-semibold text-[#2a2017]">{item.value}</p>
              </article>
            );
          })}
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
            <h2 className="text-lg font-semibold text-[#2a2017]">AR Aging</h2>
            <div className="mt-4 space-y-3">
              {Object.entries(arBuckets).map(([bucket, amount]) => (
                <div key={bucket}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-[#6f5f4b]">{bucketLabels[bucket] || bucket}</span>
                    <span className="font-semibold text-[#2a2017]">{formatCurrency(amount)}</span>
                  </div>
                  <div className="mt-1 h-2 rounded-full bg-[#f0ebe3]">
                    <div className="h-2 rounded-full bg-[#a96a14]" style={{ width: `${Math.min(100, (amount / Math.max(data?.ar?.total_open || 1, 1)) * 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
            <h2 className="text-lg font-semibold text-[#2a2017]">AP Aging</h2>
            <div className="mt-4 space-y-3">
              {Object.entries(apBuckets).map(([bucket, amount]) => (
                <div key={bucket}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-[#6f5f4b]">{bucketLabels[bucket] || bucket}</span>
                    <span className="font-semibold text-[#2a2017]">{formatCurrency(amount)}</span>
                  </div>
                  <div className="mt-1 h-2 rounded-full bg-[#f0ebe3]">
                    <div className="h-2 rounded-full bg-[#7d4f13]" style={{ width: `${Math.min(100, (amount / Math.max(data?.ap?.total_open || 1, 1)) * 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
          <h2 className="text-lg font-semibold text-[#2a2017]">Overdue receivables</h2>
          <div className="mt-4 space-y-2">
            {(data?.overdue_receivables || []).slice(0, 8).map((item) => (
              <div key={item.invoice_id} className="flex items-center justify-between rounded-xl border border-[#e8dcc9] bg-[#fff8ec] px-4 py-3 text-sm">
                <div>
                  <p className="font-medium text-[#2a2017]">{item.invoice_number}</p>
                  <p className="text-xs text-[#7b6d5b]">{item.days_overdue ?? 0} days overdue</p>
                </div>
                <span className="font-semibold text-[#9a461f]">{formatCurrency(item.amount_due)}</span>
              </div>
            ))}
            {(data?.overdue_receivables || []).length === 0 && <p className="text-sm text-[#6f5f4b]">No overdue receivables detected.</p>}
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
