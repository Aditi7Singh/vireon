"use client";

/**
 * GLDrilldownDrawer
 * =================
 * Side drawer that shows real General Ledger entries when a user clicks
 * on a chart category (e.g., "Marketing Expenses").
 *
 * Usage:
 *   <GLDrilldownDrawer
 *     open={drawerOpen}
 *     onClose={() => setDrawerOpen(false)}
 *     category="Marketing"
 *     companyId={companyId}
 *   />
 */

import React, { useEffect, useState } from "react";
import { ArrowDownRight, ArrowUpRight, ExternalLink, Loader2, X } from "lucide-react";

export interface GLEntry {
  id: string;
  date: string | null;
  amount: number;
  category: string;
  vendor: string;
  description: string;
  account: string;
  voucher_type: string;
  voucher_no: string;
}

interface DrilldownData {
  category: string;
  period_start: string;
  period_end: string;
  total_amount: number;
  entry_count: number;
  entries: GLEntry[];
}

interface GLDrilldownDrawerProps {
  open: boolean;
  onClose: () => void;
  category: string;
  companyId: string | null;
  periodStart?: string;
  periodEnd?: string;
}

function formatCurrency(v: number): string {
  const abs = Math.abs(v);
  const sign = v < 0 ? "-" : "";
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(1)}K`;
  return `${sign}$${abs.toFixed(2)}`;
}

function formatDate(s: string | null): string {
  if (!s) return "—";
  try {
    return new Date(s).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return s;
  }
}

export default function GLDrilldownDrawer({
  open,
  onClose,
  category,
  companyId,
  periodStart,
  periodEnd,
}: GLDrilldownDrawerProps) {
  const [data, setData] = useState<DrilldownData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !category || !companyId) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setData(null);

      try {
        const params = new URLSearchParams({
          company_id: companyId,
          category,
          ...(periodStart ? { period_start: periodStart } : {}),
          ...(periodEnd ? { period_end: periodEnd } : {}),
        });

        const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/advanced/gl/drilldown?${params}`,
          {
            headers: {
              "Content-Type": "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
          }
        );

        if (!res.ok) throw new Error(`API error ${res.status}`);
        const json = await res.json();
        setData(json);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load GL entries");
      } finally {
        setLoading(false);
      }
    };

    void fetchData();
  }, [open, category, companyId, periodStart, periodEnd]);

  // Close on Escape key
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    if (open) document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-40 bg-black/20 backdrop-blur-[2px]"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer panel */}
      <aside
        className="fixed right-0 top-0 z-50 flex h-full w-full max-w-xl flex-col bg-[#fffdf8] shadow-[−8px_0_40px_rgba(60,45,24,0.15)]"
        style={{ borderLeft: "1px solid #ddd2c2" }}
        role="dialog"
        aria-modal="true"
        aria-label={`GL entries for ${category}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#e8dfce] px-5 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#8c6130]">
              GL Drill-Down
            </p>
            <h2 className="text-lg font-semibold text-[#2a1f14]">{category}</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-xl p-1.5 text-[#7a6252] transition hover:bg-[#f3ead9] hover:text-[#3d2f1e]"
            aria-label="Close drawer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Summary strip */}
        {data && (
          <div className="grid grid-cols-3 gap-px bg-[#ede8df]">
            {[
              { label: "Total", value: formatCurrency(data.total_amount) },
              { label: "Entries", value: String(data.entry_count) },
              {
                label: "Period",
                value: `${formatDate(data.period_start)} – ${formatDate(data.period_end)}`,
              },
            ].map((stat) => (
              <div key={stat.label} className="bg-[#fffdf8] px-4 py-3">
                <p className="text-xs text-[#8c7a68]">{stat.label}</p>
                <p className="mt-0.5 text-sm font-semibold text-[#2a1f14]">{stat.value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 text-[#8c7a68]">
              <Loader2 className="h-7 w-7 animate-spin" />
              <p className="mt-3 text-sm">Loading GL entries…</p>
            </div>
          )}

          {error && (
            <div className="rounded-2xl border border-[#f0c0b0] bg-[#fff6f3] px-4 py-3 text-sm text-[#a04030]">
              {error}
            </div>
          )}

          {data && !loading && (
            <div className="space-y-2">
              {data.entries.length === 0 ? (
                <p className="py-8 text-center text-sm text-[#7a6252]">No GL entries found for this category.</p>
              ) : (
                data.entries.map((entry) => (
                  <article
                    key={entry.id}
                    className="rounded-2xl border border-[#ede8df] bg-[#fffcf5] p-4 transition hover:border-[#d9c9b5] hover:bg-[#fff8ec]"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center rounded-full bg-[#f4ead8] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-[#7d5020]">
                            {entry.voucher_type}
                          </span>
                          <span className="text-[10px] text-[#9a8878]">{entry.voucher_no}</span>
                        </div>
                        <p className="mt-1 truncate text-sm font-medium text-[#2a1f14]">
                          {entry.vendor}
                        </p>
                        <p className="mt-0.5 truncate text-xs text-[#7a6252]">
                          {entry.description || entry.account}
                        </p>
                      </div>

                      <div className="shrink-0 text-right">
                        <p
                          className={`text-base font-semibold ${
                            entry.amount >= 0 ? "text-[#b54f1c]" : "text-[#16a34a]"
                          }`}
                        >
                          {entry.amount >= 0 ? (
                            <ArrowDownRight className="mr-0.5 inline h-3.5 w-3.5" />
                          ) : (
                            <ArrowUpRight className="mr-0.5 inline h-3.5 w-3.5" />
                          )}
                          {formatCurrency(entry.amount)}
                        </p>
                        <p className="text-[11px] text-[#9a8878]">{formatDate(entry.date)}</p>
                      </div>
                    </div>

                    <div className="mt-2 border-t border-[#ede8df] pt-2 text-[10px] text-[#9a8878]">
                      Account: {entry.account}
                    </div>
                  </article>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-[#e8dfce] px-5 py-3">
          <p className="text-xs text-[#9a8878]">
            Showing real-time General Ledger entries from the unified data layer.
            Click any entry to open the source voucher.
          </p>
        </div>
      </aside>
    </>
  );
}
