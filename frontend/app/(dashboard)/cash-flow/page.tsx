"use client";

import { useCallback, useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import SankeyChart, { SankeyLink, SankeyNode } from "@/components/SankeyChart";
import GLDrilldownDrawer from "@/components/GLDrilldownDrawer";
import api, { APIError, API_V1_BASE, ForecastPoint } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import {
  ArrowUpRight,
  BrainCircuit,
  CalendarClock,
  Info,
  RefreshCw,
  Sparkles,
  TrendingDown,
  Wallet,
} from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

// ── Types ────────────────────────────────────────────────────────────────────

interface SankeyData {
  nodes: SankeyNode[];
  links: SankeyLink[];
  summary: {
    revenue: number;
    total_opex: number;
    gross_profit: number;
    net_profit: number;
  };
}

// ── Helpers ──────────────────────────────────────────────────────────────────

async function fetchSankeyData(companyId: string): Promise<SankeyData> {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  const res = await fetch(
    `${API_V1_BASE}/advanced/cash-flow/sankey?company_id=${companyId}`,
    {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    }
  );
  if (!res.ok) throw new Error(`Sankey API error ${res.status}`);
  return res.json();
}

// ── Fallback demo Sankey (when no backend available) ─────────────────────────

const DEMO_SANKEY: SankeyData = {
  nodes: [
    { id: "Revenue",    label: "Revenue" },
    { id: "COGS",       label: "COGS" },
    { id: "GrossProfit",label: "Gross Profit" },
    { id: "RD",         label: "R&D" },
    { id: "SalesMktg",  label: "Sales & Mktg" },
    { id: "GA",         label: "G&A" },
    { id: "NetLoss",    label: "Net Loss" },
  ],
  links: [
    { source: "Revenue",      target: "COGS",        value: 95000 },
    { source: "Revenue",      target: "GrossProfit",  value: 285000 },
    { source: "GrossProfit",  target: "RD",           value: 108000 },
    { source: "GrossProfit",  target: "SalesMktg",    value: 87000 },
    { source: "GrossProfit",  target: "GA",           value: 53000 },
    { source: "GrossProfit",  target: "NetLoss",       value: 37000 },
  ],
  summary: { revenue: 380000, total_opex: 620000, gross_profit: 285000, net_profit: -240000 },
};

function isAuthorizationError(error: unknown) {
  return error instanceof APIError && (error.status === 401 || error.status === 403);
}

// ── Page component ────────────────────────────────────────────────────────────

export default function CashFlowPage() {
  const { openChat } = useAppStore();
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [baseline, setBaseline] = useState<{ cash: number; revenue: number; expenses: number }>({
    cash: 0, revenue: 0, expenses: 0,
  });
  const [sankeyData, setSankeyData] = useState<SankeyData>(DEMO_SANKEY);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Drill-down drawer state
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerCategory, setDrawerCategory] = useState("");

  const handleNodeClick = useCallback(
    (nodeId: string) => {
      if (!companyId) return;
      setDrawerCategory(nodeId);
      setDrawerOpen(true);
    },
    [companyId]
  );

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const health = await api.getStartupHealth();
        const resolvedCompanyId = health.default_company_id || "demo-company";
        setCompanyId(resolvedCompanyId);

        const [scorecard, forecastRows, sankey] = await Promise.allSettled([
          api.getScorecard(),
          api.getForecasts(resolvedCompanyId, 6),
          fetchSankeyData(resolvedCompanyId),
        ]);

        if (scorecard.status === "fulfilled") {
          setBaseline({
            cash: scorecard.value.total_cash,
            revenue: scorecard.value.monthly_revenue,
            expenses: scorecard.value.monthly_gross_burn,
          });
        }
        if (forecastRows.status === "fulfilled") setForecast(forecastRows.value || []);
        if (sankey.status === "fulfilled") setSankeyData(sankey.value);
      } catch (e) {
        if (isAuthorizationError(e)) {
          setCompanyId(null);
          setBaseline({ cash: 0, revenue: 0, expenses: 0 });
          setForecast([]);
          setSankeyData(DEMO_SANKEY);
          setError("Cash flow data is protected. Sign in with a valid account to load the live view.");
          return;
        }

        setCompanyId("demo-company");
        setBaseline({ cash: 9230000, revenue: 1677000, expenses: 1869000 });
        setForecast([]);
        setSankeyData(DEMO_SANKEY);
        setError("Using demo cash-flow data while the backend reconnects.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const chartData = forecast.map((point: ForecastPoint) => ({
    month: new Date(point.forecast_date).toLocaleDateString(undefined, { month: "short" }),
    cash: point.cash_predicted,
    lower: point.confidence_lower,
    upper: point.confidence_upper,
  }));

  const lastPoint = forecast[forecast.length - 1];
  const netProfit = sankeyData.summary.net_profit;

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Cash Flow Analysis" />
      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* ── Hero ── */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <CalendarClock className="h-3.5 w-3.5" />
                Cash position, flows & forward forecast
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">
                Cash flow intelligence
              </h1>
              <p className="mt-2 text-sm text-[#5f5344]">
                Sankey cash flow map, forward projections, and GL drill-down.
                Click any node in the Sankey to inspect real GL entries.
              </p>
            </div>
            <button
              onClick={() =>
                openChat(
                  "Explain our cash flow, identify the top risk, and suggest a 90-day cash plan."
                )
              }
              className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
            >
              <Sparkles className="h-4 w-4" />
              Ask Finley
            </button>
          </div>
        </section>

        {error && (
          <div className="rounded-2xl border border-[#ebc1b8] bg-[#fff1ee] px-4 py-3 text-sm text-[#9f3f30]">
            {error}
          </div>
        )}

        {/* ── KPI cards ── */}
        <section className="grid gap-4 md:grid-cols-3">
          {[
            { label: "Baseline cash",    value: formatCurrency(baseline.cash),     icon: Wallet },
            { label: "Monthly revenue",  value: formatCurrency(baseline.revenue),  icon: ArrowUpRight },
            { label: "Monthly burn",     value: formatCurrency(baseline.expenses), icon: TrendingDown },
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

        {/* ── Sankey Diagram ── */}
        <section className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 shadow-[0_8px_24px_rgba(60,45,24,0.07)]">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-[#2a2017]">Cash Flow Map</h2>
              <p className="text-xs text-[#7e715f]">
                Revenue → Cost buckets → Net outcome.{" "}
                <span className="font-medium text-[#8c5c19]">Click a node</span> to drill into GL entries.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`rounded-full px-3 py-1 text-xs font-semibold ${
                  netProfit >= 0
                    ? "bg-[#dcfce7] text-[#16a34a]"
                    : "bg-[#fee2e2] text-[#dc2626]"
                }`}
              >
                Net {netProfit >= 0 ? "Profit" : "Loss"}: {formatCurrency(Math.abs(netProfit))}
              </span>
              <div className="flex items-center gap-1 text-xs text-[#9a8878]">
                <Info className="h-3.5 w-3.5" />
                <span>Click nodes for GL details</span>
              </div>
            </div>
          </div>

          <div className="h-[360px] w-full">
            <SankeyChart
              nodes={sankeyData.nodes}
              links={sankeyData.links}
              height={340}
              onNodeClick={handleNodeClick}
            />
          </div>

          {/* Legend */}
          <div className="mt-3 flex flex-wrap gap-4 border-t border-[#ede8df] pt-3">
            {sankeyData.nodes.map((n) => (
              <button
                key={n.id}
                onClick={() => handleNodeClick(n.id)}
                className="flex items-center gap-1.5 text-xs text-[#7a6252] transition hover:text-[#2a2017]"
              >
                <span className="inline-block h-2.5 w-2.5 rounded-sm bg-current" />
                {n.label}
              </button>
            ))}
          </div>
        </section>

        {/* ── Forecast trajectory + notes ── */}
        <section className="grid gap-4 lg:grid-cols-3">
          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 lg:col-span-2">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-[#2a2017]">Projected Cash Trajectory</h2>
                <p className="text-xs text-[#7e715f]">
                  Forecast confidence band from the ensemble model (SARIMA + Prophet).
                </p>
              </div>
              {lastPoint && (
                <span className="rounded-full bg-[#f4e7d8] px-2.5 py-1 text-xs font-semibold text-[#7d4f13]">
                  Month {forecast.length}
                </span>
              )}
            </div>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="cashForecastFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#ba7a1a" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#ba7a1a" stopOpacity={0.03} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 12 }} />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    tick={{ fill: "#7b6d5b", fontSize: 12 }}
                    tickFormatter={(v) => `$${Math.round(Number(v) / 1000)}k`}
                  />
                  <Tooltip
                    contentStyle={{ border: "1px solid #dbcdb9", borderRadius: 12, background: "#fff8ea" }}
                    formatter={(value: number) => formatCurrency(value)}
                  />
                  <Area type="monotone" dataKey="cash" stroke="#a96a14" strokeWidth={2.2} fill="url(#cashForecastFill)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </article>

          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[#2a2017]">Flow Summary</h2>
              <BrainCircuit className="h-4 w-4 text-[#87602a]" />
            </div>
            <div className="space-y-3 text-sm text-[#5f5344]">
              {[
                { label: "Revenue",      value: formatCurrency(sankeyData.summary.revenue),      positive: true  },
                { label: "Total OpEx",   value: formatCurrency(sankeyData.summary.total_opex),   positive: false },
                { label: "Gross Profit", value: formatCurrency(sankeyData.summary.gross_profit), positive: sankeyData.summary.gross_profit >= 0 },
                { label: "Net P&L",      value: formatCurrency(Math.abs(sankeyData.summary.net_profit)),
                  positive: sankeyData.summary.net_profit >= 0, prefix: sankeyData.summary.net_profit >= 0 ? "+" : "−" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between rounded-xl border border-[#ede8df] px-3 py-2">
                  <span className="text-xs text-[#7a6252]">{item.label}</span>
                  <span className={`text-sm font-semibold ${item.positive ? "text-[#16a34a]" : "text-[#b54f1c]"}`}>
                    {item.prefix}{item.value}
                  </span>
                </div>
              ))}
            </div>

            {forecast.length > 0 && (
              <div className="mt-3 rounded-xl border border-[#e8dcc9] bg-[#fff8ec] p-3 text-xs text-[#72522a]">
                Forecast cash in month {forecast.length}: {formatCurrency(lastPoint?.cash_predicted || 0)}
              </div>
            )}
          </article>
        </section>

        {loading && (
          <div className="flex items-center gap-2 rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-4 text-sm text-[#6f5f4b]">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading forecast data…
          </div>
        )}
      </div>

      {/* GL Drill-Down Drawer */}
      <GLDrilldownDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        category={drawerCategory}
        companyId={companyId}
      />
    </div>
  );
}
