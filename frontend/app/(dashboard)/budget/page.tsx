"use client";

import { useEffect, useMemo, useState } from "react";
import TopBar from "@/components/TopBar";
import api, { BudgetVarianceResponse } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import { BarChart3, Calculator, RefreshCw, Sparkles, TrendingDown, TrendingUp } from "lucide-react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function BudgetPage() {
  const { openChat } = useAppStore();
  const [budgetId, setBudgetId] = useState<string | null>(null);
  const [variance, setVariance] = useState<BudgetVarianceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const budgets = await api.getBudgets();
        const firstBudget = budgets?.[0];
        if (!firstBudget?.id) {
          setError("No budget available yet.");
          return;
        }
        setBudgetId(String(firstBudget.id));
        setVariance(await api.getBudgetVariance(String(firstBudget.id)));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load budget data.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const chartData = useMemo(() => (variance?.variances || []).slice(0, 8).map((item) => ({
    category: item.category,
    variance: item.variance,
  })), [variance]);

  const totalVariance = (variance?.variances || []).reduce((sum, item) => sum + item.variance, 0);

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Budget vs Actual" />
      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Calculator className="h-3.5 w-3.5" />
                Budget discipline and variance review
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Budget vs actual</h1>
              <p className="mt-2 text-sm text-[#5f5344]">Identify the lines driving budget overruns or savings.</p>
            </div>
            <button
              onClick={() => openChat("Analyze the biggest budget variances and explain which categories need action.")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
            >
              <Sparkles className="h-4 w-4" />
              Ask Finley
            </button>
          </div>
        </section>

        {error && <div className="rounded-2xl border border-[#ebc1b8] bg-[#fff1ee] px-4 py-3 text-sm text-[#9f3f30]">{error}</div>}

        <section className="grid gap-4 md:grid-cols-3">
          {[
            { label: "Budget", value: variance?.budget_name || "—", icon: BarChart3 },
            { label: "Total variance", value: formatCurrency(totalVariance), icon: totalVariance >= 0 ? TrendingUp : TrendingDown },
            { label: "Active budget id", value: budgetId || "—", icon: Calculator },
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
          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 lg:col-span-1">
            <h2 className="text-lg font-semibold text-[#2a2017]">Variance by category</h2>
            <div className="mt-4 h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <XAxis type="number" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 12 }} />
                  <YAxis type="category" dataKey="category" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 12 }} width={120} />
                  <Tooltip contentStyle={{ border: "1px solid #dbcdb9", borderRadius: 12, background: "#fff8ea" }} formatter={(value: number) => formatCurrency(value)} />
                  <Bar dataKey="variance" fill="#a96a14" radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </article>

          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
            <h2 className="text-lg font-semibold text-[#2a2017]">Variance table</h2>
            <div className="mt-4 space-y-2">
              {(variance?.variances || []).map((item) => (
                <div key={item.category} className="rounded-xl border border-[#e8dcc9] bg-[#fff8ec] px-4 py-3 text-sm">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-medium text-[#2a2017]">{item.category}</p>
                      <p className="text-xs text-[#7b6d5b]">Budget {formatCurrency(item.budget)} vs actual {formatCurrency(item.actual)}</p>
                    </div>
                    <div className={cn("text-right font-semibold", item.variance >= 0 ? "text-[#9a461f]" : "text-[#1f7a41]")}>{formatCurrency(item.variance)}</div>
                  </div>
                </div>
              ))}
              {(variance?.variances || []).length === 0 && <p className="text-sm text-[#6f5f4b]">No budget variance data available.</p>}
            </div>
          </article>
        </section>

        {loading && (
          <div className="flex items-center gap-2 rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-4 text-sm text-[#6f5f4b]">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading budget data...
          </div>
        )}
      </div>
    </div>
  );
}
