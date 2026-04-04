"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import api, { ForecastPoint } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import { ArrowUpRight, BrainCircuit, CalendarClock, RefreshCw, Sparkles, TrendingDown, Wallet } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function CashFlowPage() {
  const { openChat } = useAppStore();
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [baseline, setBaseline] = useState<{ cash: number; revenue: number; expenses: number }>({ cash: 0, revenue: 0, expenses: 0 });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

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

        const [scorecard, forecastRows] = await Promise.all([
          api.getScorecard(),
          api.getForecasts(resolvedCompanyId, 6),
        ]);

        setBaseline({
          cash: scorecard.total_cash,
          revenue: scorecard.monthly_revenue,
          expenses: scorecard.monthly_gross_burn,
        });
        setForecast(forecastRows || []);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load cash flow data.");
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

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Cash Flow Forecast" />
      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <CalendarClock className="h-3.5 w-3.5" />
                Cash position and forward forecast
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Cash flow runway planning</h1>
              <p className="mt-2 text-sm text-[#5f5344]">
                Forward projections from the current ledger baseline with a simple monthly trend model.
              </p>
            </div>
            <button
              onClick={() => openChat("Explain our cash flow forecast, identify the most important risk, and suggest a 90-day cash plan.")}
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

        <section className="grid gap-4 md:grid-cols-3">
          {[
            { label: "Baseline cash", value: formatCurrency(baseline.cash), icon: Wallet },
            { label: "Baseline revenue", value: formatCurrency(baseline.revenue), icon: ArrowUpRight },
            { label: "Baseline burn", value: formatCurrency(baseline.expenses), icon: TrendingDown },
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

        <section className="grid gap-4 lg:grid-cols-3">
          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 lg:col-span-2">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-[#2a2017]">Projected Cash Trajectory</h2>
                <p className="text-xs text-[#7e715f]">Forecast confidence band uses the model outputs returned by planning services.</p>
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
                      <stop offset="5%" stopColor="#ba7a1a" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#ba7a1a" stopOpacity={0.03} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 12 }} />
                  <YAxis tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 12 }} tickFormatter={(value) => `$${Math.round(Number(value) / 1000)}k`} />
                  <Tooltip contentStyle={{ border: "1px solid #dbcdb9", borderRadius: 12, background: "#fff8ea" }} formatter={(value: number) => formatCurrency(value)} />
                  <Area type="monotone" dataKey="cash" stroke="#a96a14" strokeWidth={2.2} fill="url(#cashForecastFill)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </article>

          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[#2a2017]">Forecast Notes</h2>
              <BrainCircuit className="h-4 w-4 text-[#87602a]" />
            </div>
            <div className="space-y-3 text-sm text-[#5f5344]">
              <p>Model: deterministic trend from the latest monthly metrics.</p>
              <p>Baseline runway check: use the current cash balance and net burn from the dashboard summary.</p>
              <p>Confidence band: upper and lower cash bands returned by the forecast endpoint.</p>
              {forecast.length > 0 && (
                <div className="rounded-xl border border-[#e8dcc9] bg-[#fff8ec] p-3 text-xs text-[#72522a]">
                  Latest forecast cash: {formatCurrency(lastPoint?.cash_predicted || 0)}
                </div>
              )}
            </div>
          </article>
        </section>

        {loading && (
          <div className="flex items-center gap-2 rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-4 text-sm text-[#6f5f4b]">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading forecast data...
          </div>
        )}
      </div>
    </div>
  );
}
