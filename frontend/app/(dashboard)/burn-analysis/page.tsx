"use client";

/**
 * Burn Analysis Page
 * ==================
 * Features:
 * - Waterfall chart: month-over-month burn vs revenue
 * - Clicking a bar opens a GL drill-down drawer for that period
 * - Key burn metrics KPIs
 * - Strategist Agent quick-access for scenario planning
 */

import { useCallback, useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import WaterfallChart, { WaterfallRow } from "@/components/WaterfallChart";
import GLDrilldownDrawer from "@/components/GLDrilldownDrawer";
import { useAppStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import api, { API_V1_BASE } from "@/lib/api";
import {
  BrainCircuit,
  ChevronRight,
  FlameKindling,
  Loader2,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────────

interface BurnMetrics {
  avg_monthly_burn: number;
  avg_monthly_revenue: number;
  burn_multiple: number;
  worst_month: string;
  best_month: string;
  trend_direction: "improving" | "worsening" | "stable";
}

// ── Helpers ──────────────────────────────────────────────────────────────────

async function fetchWaterfallData(companyId: string, months: number): Promise<WaterfallRow[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  const res = await fetch(
    `${API_V1_BASE}/advanced/burn-analysis/waterfall?company_id=${companyId}&months=${months}`,
    {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    }
  );
  if (!res.ok) throw new Error(`Waterfall API error ${res.status}`);
  const data = await res.json();
  return data.waterfall as WaterfallRow[];
}

function computeMetrics(rows: WaterfallRow[]): BurnMetrics {
  if (rows.length === 0) {
    return {
      avg_monthly_burn: 0,
      avg_monthly_revenue: 0,
      burn_multiple: 0,
      worst_month: "—",
      best_month: "—",
      trend_direction: "stable",
    };
  }
  const avgBurn = rows.reduce((s, r) => s + r.burn, 0) / rows.length;
  const avgRevenue = rows.reduce((s, r) => s + r.revenue, 0) / rows.length;
  const burnMultiple = avgRevenue > 0 ? avgBurn / avgRevenue : 0;

  const worstRow = rows.reduce((a, b) => (b.net_change < a.net_change ? b : a));
  const bestRow = rows.reduce((a, b) => (b.net_change > a.net_change ? b : a));

  // Trend: compare last 2 net_change values
  let trend: "improving" | "worsening" | "stable" = "stable";
  if (rows.length >= 2) {
    const last = rows[rows.length - 1].net_change;
    const prev = rows[rows.length - 2].net_change;
    if (last > prev + 5000) trend = "improving";
    else if (last < prev - 5000) trend = "worsening";
  }

  return {
    avg_monthly_burn: avgBurn,
    avg_monthly_revenue: avgRevenue,
    burn_multiple: burnMultiple,
    worst_month: worstRow.month,
    best_month: bestRow.month,
    trend_direction: trend,
  };
}

// ── Demo data fallback ────────────────────────────────────────────────────────

const DEMO_WATERFALL: WaterfallRow[] = [
  { month: "Nov 24", starting_cash: 4200000, revenue: 340000, burn: 625000, net_change: -285000, ending_cash: 3915000 },
  { month: "Dec 24", starting_cash: 3915000, revenue: 360000, burn: 618000, net_change: -258000, ending_cash: 3657000 },
  { month: "Jan 25", starting_cash: 3657000, revenue: 375000, burn: 605000, net_change: -230000, ending_cash: 3427000 },
  { month: "Feb 25", starting_cash: 3427000, revenue: 380000, burn: 598000, net_change: -218000, ending_cash: 3209000 },
  { month: "Mar 25", starting_cash: 3209000, revenue: 395000, burn: 590000, net_change: -195000, ending_cash: 3014000 },
  { month: "Apr 25", starting_cash: 3014000, revenue: 410000, burn: 582000, net_change: -172000, ending_cash: 2842000 },
];

// ── Page component ────────────────────────────────────────────────────────────

export default function BurnAnalysisPage() {
  const { openChat } = useAppStore();
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [waterfall, setWaterfall] = useState<WaterfallRow[]>(DEMO_WATERFALL);
  const [metrics, setMetrics] = useState<BurnMetrics>(computeMetrics(DEMO_WATERFALL));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // GL drill-down drawer
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerCategory, setDrawerCategory] = useState("");
  const [drawerPeriod, setDrawerPeriod] = useState<{ start: string; end: string } | undefined>();

  const handleBarClick = useCallback(
    (month: string, type: "revenue" | "burn") => {
      if (!companyId) return;
      setDrawerCategory(type === "burn" ? "OpEx" : "Revenue");
      // Approximate: set period as that single month
      setDrawerPeriod(undefined);
      setDrawerOpen(true);
    },
    [companyId]
  );

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const h = await api.getStartupHealth();
        const resolvedId = h.default_company_id || "demo-company";
        setCompanyId(resolvedId);

        if (resolvedId !== "demo-company") {
          const rows = await fetchWaterfallData(resolvedId, 6);
          if (rows.length > 0) {
            setWaterfall(rows);
            setMetrics(computeMetrics(rows));
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load burn data.");
        // Keep demo data visible
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const trendColor =
    metrics.trend_direction === "improving"
      ? "text-[#16a34a]"
      : metrics.trend_direction === "worsening"
        ? "text-[#dc2626]"
        : "text-[#92400e]";

  const TrendIcon =
    metrics.trend_direction === "improving" ? TrendingUp : TrendingDown;

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Burn Analysis" />
      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* ── Hero ── */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <FlameKindling className="h-3.5 w-3.5" />
                Month-over-month burn analysis
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Burn Analysis</h1>
              <p className="mt-2 text-sm text-[#5f5344]">
                Waterfall view of cash changes month by month.{" "}
                <span className="font-medium text-[#8c5c19]">Click a bar</span> to drill into
                the underlying GL entries.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() =>
                  openChat(
                    "Analyse our burn rate trend and suggest the top 3 areas to cut spend this quarter."
                  )
                }
                className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
              >
                <Sparkles className="h-4 w-4" />
                Ask Finley
              </button>
              <button
                onClick={() =>
                  openChat(
                    "Run a scenario: what happens to runway if we cut burn by 15% starting next month?"
                  )
                }
                className="inline-flex items-center gap-2 rounded-xl border border-[#c8a96a] bg-[#fff8ea] px-4 py-2.5 text-sm font-medium text-[#5a3a0e] hover:bg-[#f5edd5]"
              >
                <BrainCircuit className="h-4 w-4" />
                Run Scenario
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </section>

        {error && (
          <div className="rounded-2xl border border-[#ebc1b8] bg-[#fff1ee] px-4 py-3 text-sm text-[#9f3f30]">
            {error} — showing demo data.
          </div>
        )}

        {/* ── KPI cards ── */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            {
              label: "Avg Monthly Burn",
              value: formatCurrency(metrics.avg_monthly_burn),
              sub: "6-month average",
              icon: TrendingDown,
              negative: true,
            },
            {
              label: "Avg Monthly Revenue",
              value: formatCurrency(metrics.avg_monthly_revenue),
              sub: "6-month average",
              icon: TrendingUp,
              negative: false,
            },
            {
              label: "Burn Multiple",
              value: `${metrics.burn_multiple.toFixed(2)}x`,
              sub: "Burn ÷ Revenue",
              icon: FlameKindling,
              negative: metrics.burn_multiple > 1.5,
            },
            {
              label: "Trend",
              value: metrics.trend_direction.charAt(0).toUpperCase() + metrics.trend_direction.slice(1),
              sub: `Best: ${metrics.best_month} · Worst: ${metrics.worst_month}`,
              icon: TrendIcon,
              negative: metrics.trend_direction === "worsening",
            },
          ].map((card) => {
            const Icon = card.icon;
            return (
              <article key={card.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{card.label}</p>
                  <Icon className={`h-4 w-4 ${card.negative ? "text-[#b54f1c]" : "text-[#16a34a]"}`} />
                </div>
                <p className={`mt-2 text-2xl font-semibold ${card.negative ? "text-[#b54f1c]" : "text-[#2a2017]"}`}>
                  {card.value}
                </p>
                <p className="mt-0.5 text-xs text-[#9a8878]">{card.sub}</p>
              </article>
            );
          })}
        </section>

        {/* ── Waterfall chart ── */}
        <section className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 shadow-[0_8px_24px_rgba(60,45,24,0.07)]">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-[#2a2017]">Month-over-Month Cash Waterfall</h2>
              <p className="text-xs text-[#7e715f]">
                Green = Revenue inflow · Red = Burn outflow.{" "}
                <span className="font-medium text-[#8c5c19]">Click a bar</span> to drill into GL entries.
              </p>
            </div>
            <span className={`flex items-center gap-1.5 text-sm font-semibold ${trendColor}`}>
              <TrendIcon className="h-4 w-4" />
              {metrics.trend_direction.charAt(0).toUpperCase() + metrics.trend_direction.slice(1)}
            </span>
          </div>

          {loading ? (
            <div className="flex h-[320px] items-center justify-center">
              <Loader2 className="h-7 w-7 animate-spin text-[#8c6130]" />
            </div>
          ) : (
            <WaterfallChart
              data={waterfall}
              onBarClick={handleBarClick}
              height={320}
            />
          )}

          {/* Month summary table */}
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[#ede8df]">
                  {["Month", "Revenue", "Burn", "Net Change", "End Cash"].map((h) => (
                    <th key={h} className="pb-2 text-left font-semibold text-[#7a6252]">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {waterfall.map((row) => (
                  <tr key={row.month} className="border-b border-[#f0e9df] hover:bg-[#fdf8f0]">
                    <td className="py-2 font-medium text-[#2a2017]">{row.month}</td>
                    <td className="py-2 text-[#16a34a]">{formatCurrency(row.revenue)}</td>
                    <td className="py-2 text-[#b54f1c]">{formatCurrency(row.burn)}</td>
                    <td className={`py-2 font-semibold ${row.net_change >= 0 ? "text-[#16a34a]" : "text-[#b54f1c]"}`}>
                      {row.net_change >= 0 ? "+" : ""}{formatCurrency(row.net_change)}
                    </td>
                    <td className="py-2 text-[#2a2017]">{formatCurrency(row.ending_cash)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

      </div>

      {/* GL Drill-Down Drawer */}
      <GLDrilldownDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        category={drawerCategory}
        companyId={companyId}
        periodStart={drawerPeriod?.start}
        periodEnd={drawerPeriod?.end}
      />
    </div>
  );
}
