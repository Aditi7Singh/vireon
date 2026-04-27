"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { useExpenses, useAlerts } from "@/hooks/useFinancialData";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import {
  Receipt, ShieldCheck, Sparkles, Users, Globe, Layers,
  Zap, Tag, AlertTriangle, Copy, TrendingUp, TrendingDown,
  Filter, Download, Plus, ChevronRight,
} from "lucide-react";
import type { ElementType } from "react";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

const COLORS = ["#bf7a1d", "#227a66", "#9d6328", "#ac4e23", "#5f7c2f", "#7a5f2e", "#85561a"];

const categoryMeta: Record<string, { label: string; icon: ElementType; color: string }> = {
  payroll:   { label: "Payroll",      icon: Users,       color: "#bf7a1d" },
  aws:       { label: "Infrastructure", icon: Globe,      color: "#227a66" },
  saas:      { label: "SaaS",         icon: Layers,      color: "#9d6328" },
  marketing: { label: "Marketing",    icon: Zap,         color: "#ac4e23" },
  office:    { label: "Office",       icon: Tag,         color: "#5f7c2f" },
  hiring:    { label: "Hiring",       icon: Users,       color: "#7a5f2e" },
  legal:     { label: "Legal",        icon: ShieldCheck, color: "#85561a" },
};

const MONTHLY_TREND = [
  { month: "Nov", payroll: 4200000, aws: 680000, saas: 320000, marketing: 850000, other: 410000 },
  { month: "Dec", payroll: 4200000, aws: 720000, saas: 340000, marketing: 920000, other: 430000 },
  { month: "Jan", payroll: 4500000, aws: 750000, saas: 360000, marketing: 1050000, other: 450000 },
  { month: "Feb", payroll: 4500000, aws: 780000, saas: 370000, marketing: 980000, other: 460000 },
  { month: "Mar", payroll: 4800000, aws: 820000, saas: 390000, marketing: 1120000, other: 490000 },
  { month: "Apr", payroll: 4800000, aws: 850000, saas: 410000, marketing: 1240000, other: 510000 },
];

const CUSTOM_TOOLTIP = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const total = payload.reduce((s: number, p: any) => s + (p.value || 0), 0);
  return (
    <div className="rounded-xl border border-[#e4d6c4] bg-white p-3 shadow-xl text-xs">
      <p className="font-bold text-[#2a2017] mb-1.5">{label}</p>
      {payload.map((p: any) => (
        <div key={p.name} className="flex items-center justify-between gap-4 py-0.5">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ background: p.fill }} />
            <span className="text-[#6b5b4a] capitalize">{p.name}</span>
          </span>
          <span className="font-semibold text-[#2a2017]">₹{(p.value / 100000).toFixed(1)}L</span>
        </div>
      ))}
      <div className="border-t border-[#ede8e0] mt-1.5 pt-1.5 flex justify-between">
        <span className="text-[#8b7a69]">Total</span>
        <span className="font-bold text-[#8d4f27]">₹{(total / 100000).toFixed(1)}L</span>
      </div>
    </div>
  );
};

const PIE_TOOLTIP = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  return (
    <div className="rounded-xl border border-[#e4d6c4] bg-white p-3 shadow-xl text-xs">
      <p className="font-bold text-[#2a2017] capitalize">{item.name}</p>
      <p className="text-[#8d4f27] font-semibold mt-0.5">₹{(item.value / 100000).toFixed(1)}L ({item.payload.pct}%)</p>
    </div>
  );
};

export default function ExpensesPage() {
  const [department, setDepartment] = useState<string>("all");
  const [activeView, setActiveView] = useState<"breakdown" | "trend">("breakdown");
  const { expenses } = useExpenses(3, department === "all" ? undefined : { department });
  const { alerts } = useAlerts();
  const { openChat } = useAppStore();

  const expenseAlerts = alerts.alerts.filter(a =>
    ["spending_spike", "duplicate_invoice"].includes(a.alert_type)
  );

  const totalExpenses = Object.values(expenses.breakdown as Record<string, number>)
    .reduce((a: number, b: number) => a + b, 0);

  const nonZeroBreakdown = Object.entries(expenses.breakdown as Record<string, number>)
    .filter(([, amount]) => Number(amount || 0) > 0)
    .sort((a, b) => Number(b[1]) - Number(a[1]));

  const pieData = nonZeroBreakdown.map(([key, value], i) => ({
    name: categoryMeta[key]?.label || key,
    value: Number(value),
    color: COLORS[i % COLORS.length],
    pct: totalExpenses > 0 ? Math.round((Number(value) / totalExpenses) * 100) : 0,
  }));

  const topTwo = nonZeroBreakdown.slice(0, 2);
  const departments = ["all", "Engineering", "Marketing", "Sales", "Operations", "Finance"];

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Expense Control Center" subtitle="Capital allocations & spend analytics" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* Hero */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Receipt className="h-3.5 w-3.5" />
                Audited expense ledger · FY 2025-26
              </p>
              <h1 className="text-3xl font-semibold text-[#2c2013]">Expense Control Center</h1>
              <p className="text-sm text-[#5f5344]">
                Total outflow this cycle: <span className="font-bold text-[#2a2017]">{formatCurrency(totalExpenses)}</span>
              </p>
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-[#7a664f]">Department:</span>
                <select
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="rounded-lg border border-[#cebda8] bg-white px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20"
                >
                  {departments.map(d => (
                    <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex gap-3">
              <button className="inline-flex items-center gap-2 rounded-xl border border-[#cebda8] bg-white px-4 py-2.5 text-sm font-medium text-[#4a3f35] hover:bg-[#faf5ec]">
                <Download className="h-4 w-4" />
                Export
              </button>
              <button className="inline-flex items-center gap-2 rounded-xl border border-[#cebda8] bg-white px-4 py-2.5 text-sm font-medium text-[#4a3f35] hover:bg-[#faf5ec]">
                <Plus className="h-4 w-4" />
                Add Expense
              </button>
              <button
                onClick={() => openChat("Optimize expenditures")}
                className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
              >
                <Sparkles className="h-4 w-4" />
                AI Audit
              </button>
            </div>
          </div>
        </section>

        {/* KPI Cards */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Total Expenses", value: formatCurrency(totalExpenses), sub: "This billing cycle", icon: Receipt, trend: "+4.2%", up: true },
            {
              label: topTwo[0] ? `${categoryMeta[topTwo[0][0]]?.label || topTwo[0][0]}` : "Top Category",
              value: topTwo[0] ? `${Math.round((Number(topTwo[0][1]) / Math.max(totalExpenses, 1)) * 100)}%` : "—",
              sub: topTwo[0] ? formatCurrency(Number(topTwo[0][1])) : "No data",
              icon: Users, trend: "-1.2%", up: false,
            },
            {
              label: topTwo[1] ? `${categoryMeta[topTwo[1][0]]?.label || topTwo[1][0]}` : "2nd Category",
              value: topTwo[1] ? `${Math.round((Number(topTwo[1][1]) / Math.max(totalExpenses, 1)) * 100)}%` : "—",
              sub: topTwo[1] ? formatCurrency(Number(topTwo[1][1])) : "No data",
              icon: Layers, trend: "+8.1%", up: true,
            },
            { label: "Compliance Score", value: "98%", sub: "Audited & reviewed", icon: ShieldCheck, trend: "+2pts", up: true },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <article key={item.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="p-2 rounded-xl bg-[#f6efe5]">
                    <Icon className="h-4 w-4 text-[#8d4f27]" />
                  </div>
                  <span className={cn("text-xs font-semibold flex items-center gap-0.5", item.up ? "text-emerald-600" : "text-rose-600")}>
                    {item.up ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    {item.trend}
                  </span>
                </div>
                <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a] mb-1">{item.label}</p>
                <p className="text-2xl font-bold text-[#2a2017]">{item.value}</p>
                <p className="text-xs text-[#8b7a69] mt-0.5">{item.sub}</p>
              </article>
            );
          })}
        </section>

        {/* Charts */}
        <section className="grid gap-6 lg:grid-cols-2">
          {/* Donut breakdown */}
          <div className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-sm font-bold text-[#2a2017]">Spend Breakdown</h3>
                <p className="text-xs text-[#8b7a69]">By category this cycle</p>
              </div>
              <div className="flex gap-1.5">
                <button
                  onClick={() => setActiveView("breakdown")}
                  className={cn("px-3 py-1 rounded-lg text-xs font-semibold transition-all", activeView === "breakdown" ? "bg-[#231c15] text-white" : "bg-[#f6efe5] text-[#776b5a] hover:bg-[#eee6d8]")}
                >
                  Donut
                </button>
                <button
                  onClick={() => setActiveView("trend")}
                  className={cn("px-3 py-1 rounded-lg text-xs font-semibold transition-all", activeView === "trend" ? "bg-[#231c15] text-white" : "bg-[#f6efe5] text-[#776b5a] hover:bg-[#eee6d8]")}
                >
                  Trend
                </button>
              </div>
            </div>

            {activeView === "breakdown" ? (
              pieData.length > 0 ? (
                <div className="flex items-center gap-4">
                  <div style={{ width: 200, height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={2} dataKey="value">
                          {pieData.map((entry, i) => (
                            <Cell key={i} fill={entry.color} stroke="none" />
                          ))}
                        </Pie>
                        <Tooltip content={<PIE_TOOLTIP />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex-1 space-y-2">
                    {pieData.map((entry) => (
                      <div key={entry.name} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: entry.color }} />
                          <span className="text-xs text-[#5f5344] capitalize">{entry.name}</span>
                        </div>
                        <span className="text-xs font-bold text-[#2a2017]">{entry.pct}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-40 text-sm text-[#8b7a69]">No expense data available</div>
              )
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={MONTHLY_TREND} stackOffset="expand" barSize={22}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                  <XAxis dataKey="month" tick={{ fontSize: 10, fill: "#8b7a69" }} axisLine={false} tickLine={false} />
                  <YAxis tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 10, fill: "#8b7a69" }} axisLine={false} tickLine={false} width={36} />
                  <Tooltip content={<CUSTOM_TOOLTIP />} />
                  {["payroll", "aws", "saas", "marketing", "other"].map((key, i) => (
                    <Bar key={key} dataKey={key} stackId="a" fill={COLORS[i]} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Monthly absolute trend */}
          <div className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-6">
            <div className="mb-5">
              <h3 className="text-sm font-bold text-[#2a2017]">Monthly Expense Trend</h3>
              <p className="text-xs text-[#8b7a69]">6-month absolute spend by category (₹ Lakh)</p>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={MONTHLY_TREND} barSize={14}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 10, fill: "#8b7a69" }} axisLine={false} tickLine={false} />
                <YAxis tickFormatter={(v) => `₹${(v / 100000).toFixed(0)}L`} tick={{ fontSize: 10, fill: "#8b7a69" }} axisLine={false} tickLine={false} width={44} />
                <Tooltip content={<CUSTOM_TOOLTIP />} />
                <Legend wrapperStyle={{ fontSize: 10, paddingTop: 8 }} />
                {["payroll", "aws", "saas", "marketing", "other"].map((key, i) => (
                  <Bar key={key} dataKey={key} stackId="b" fill={COLORS[i]} radius={i === 4 ? [4, 4, 0, 0] : undefined} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Category Cards */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-[#2a2017]">Category Breakdown</h3>
            <button className="flex items-center gap-1.5 text-xs text-[#776b5a] hover:text-[#4a3f35]">
              <Filter className="h-3.5 w-3.5" /> Filter
            </button>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {nonZeroBreakdown.map(([key, amount]) => {
              const meta = categoryMeta[key] || { label: key, icon: Receipt, color: "#8a6b3f" };
              const IconComp = meta.icon;
              const pct = totalExpenses > 0 ? (Number(amount) / totalExpenses) * 100 : 0;
              return (
                <article key={key} className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 hover:border-[#cbb7a1] hover:shadow-[0_8px_16px_rgba(0,0,0,0.06)] transition-all group cursor-pointer">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 rounded-lg" style={{ backgroundColor: `${meta.color}18` }}>
                        <IconComp className="h-4 w-4" style={{ color: meta.color }} />
                      </div>
                      <p className="text-sm font-semibold text-[#2a2017]">{meta.label}</p>
                    </div>
                    <span className="text-sm font-bold text-[#2a2017]">{pct.toFixed(1)}%</span>
                  </div>
                  <p className="text-2xl font-bold text-[#2a2017] mb-4">{formatCurrency(Number(amount))}</p>
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-[#7b6d5b]">of total spend</span>
                      <ChevronRight className="h-3 w-3 text-[#8b7a69] opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <div className="w-full bg-[#f0ebe3] rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${pct}%`, backgroundColor: meta.color }}
                      />
                    </div>
                  </div>
                </article>
              );
            })}
            {nonZeroBreakdown.length === 0 && (
              <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 col-span-3">
                <p className="text-sm text-[#6f5f4b]">No categorized expense entries found for this period.</p>
              </article>
            )}
          </div>
        </section>

        {/* Anomaly Alerts */}
        {expenseAlerts.length > 0 && (
          <section className="rounded-2xl border border-[#f0dfd2] bg-[#fff9f5] p-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="h-5 w-5 text-[#9a461f]" />
              <h3 className="text-sm font-bold text-[#4a3f35]">Expense Anomalies & Audit Flags</h3>
              <span className="ml-auto rounded-full bg-[#9a461f] text-white text-[10px] font-bold px-2 py-0.5">{expenseAlerts.length}</span>
            </div>
            <div className="space-y-3">
              {expenseAlerts.map((alert) => (
                <div key={alert.id} className="flex items-start justify-between rounded-xl border border-[#f5e4d8] bg-white p-4">
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-[#fef0e8]">
                      {alert.alert_type === "duplicate_invoice" ? (
                        <Copy className="h-4 w-4 text-[#9a461f]" />
                      ) : (
                        <TrendingUp className="h-4 w-4 text-[#9a461f]" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-[#4a3f35]">{alert.description}</p>
                      <p className="text-xs text-[#7b6d5b] mt-0.5">
                        Category: {alert.category} · Deterministic Audit
                      </p>
                    </div>
                  </div>
                  <div className="text-right shrink-0 ml-4">
                    <p className="font-bold text-[#9a461f]">₹{alert.amount.toLocaleString()}</p>
                    <span className="inline-block mt-1 rounded-full bg-[#fef0e8] border border-[#f5ccb5] text-[#9a461f] text-[10px] font-bold px-2 py-0.5">
                      {alert.alert_type === "duplicate_invoice" ? "Duplicate" : "Spike"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
