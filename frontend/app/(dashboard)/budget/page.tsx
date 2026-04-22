"use client";

import { useEffect, useMemo, useState } from "react";
import TopBar from "@/components/TopBar";
import api, { BudgetVarianceResponse } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import {
  BarChart3, Calculator, RefreshCw, Sparkles, TrendingDown, TrendingUp,
  Calendar, Scale, Info,
} from "lucide-react";
import {
  Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
  CartesianGrid, Cell, Legend, LineChart, Line,
} from "recharts";

const INR = (n: number) =>
  n >= 10_000_000
    ? `₹${(n / 10_000_000).toFixed(2)}Cr`
    : n >= 100_000
    ? `₹${(n / 100_000).toFixed(1)}L`
    : `₹${n.toLocaleString("en-IN")}`;

// India FY 2025-26 monthly budget plan (Apr 2025 – Mar 2026)
const BUDGET_MONTHS = ["Apr '25", "May '25", "Jun '25", "Jul '25", "Aug '25", "Sep '25", "Oct '25", "Nov '25", "Dec '25", "Jan '26", "Feb '26", "Mar '26"];

const PROJECT_BUDGETS = [
  { id: "sprouts", name: "Sprout",  color: "#16a34a", annual: 12_000_000, headcount: 12 },
  { id: "orchard", name: "Orchard", color: "#ea580c", annual: 16_800_000, headcount: 18 },
  { id: "ai_lab",  name: "AI Lab",  color: "#7c3aed", annual:  8_400_000, headcount:  8 },
  { id: "shared",  name: "Shared",  color: "#6b7280", annual:  5_400_000, headcount:  3 },
];

const CATEGORY_BUDGETS = [
  { category: "Salaries & Benefits", budgeted: 30_960_000, color: "#f59e0b" },
  { category: "Cloud & Infra",       budgeted:  6_000_000, color: "#6366f1" },
  { category: "Office & Facilities", budgeted:  3_660_000, color: "#10b981" },
  { category: "Legal & Compliance",  budgeted:  1_056_000, color: "#f43f5e" },
  { category: "Sales & Marketing",   budgeted:  1_440_000, color: "#8b5cf6" },
  { category: "R&D (AI Lab Infra)",  budgeted:  2_400_000, color: "#0ea5e9" },
];
const TOTAL_ANNUAL_BUDGET = CATEGORY_BUDGETS.reduce((s, c) => s + c.budgeted, 0);

// Monthly spend projection (₹ crore basis — growing through FY)
const MONTHLY_PROJECTION = BUDGET_MONTHS.map((month, i) => {
  const growth = 0.88 + i * 0.011;
  return {
    month,
    budget:  Math.round(TOTAL_ANNUAL_BUDGET / 12),
    actual:  i <= 5 ? Math.round((TOTAL_ANNUAL_BUDGET / 12) * growth) : undefined,
    forecast: i >  5 ? Math.round((TOTAL_ANNUAL_BUDGET / 12) * growth) : undefined,
  };
});

// India Fiscal Calendar deadlines
const TAX_DEADLINES = [
  { date: "Apr 1, 2025",  label: "FY 2025-26 begins",              type: "milestone",   icon: "🚀" },
  { date: "Jun 15, 2025", label: "Advance Tax – 1st instalment (15%)", type: "tax",    icon: "💰" },
  { date: "Jul 31, 2025", label: "ITR filing (non-audit companies)",type: "compliance",  icon: "📋" },
  { date: "Sep 15, 2025", label: "Advance Tax – 2nd instalment (45%)", type: "tax",    icon: "💰" },
  { date: "Oct 15, 2025", label: "Tax Audit Report (Form 3CA/3CD)",  type: "compliance", icon: "📋" },
  { date: "Oct 31, 2025", label: "ITR filing (audit companies)",    type: "compliance",  icon: "📋" },
  { date: "Dec 15, 2025", label: "Advance Tax – 3rd instalment (75%)", type: "tax",    icon: "💰" },
  { date: "Mar 15, 2026", label: "Advance Tax – 4th instalment (100%)", type: "tax",   icon: "💰" },
  { date: "Mar 31, 2026", label: "FY 2025-26 ends · Close accounts",type: "milestone",  icon: "🏁" },
];

const COMPLIANCE_RULES = [
  { label: "Advance Corporate Tax Rate",   value: "25% + surcharge",   note: "Section 115BA — startup relief possible" },
  { label: "TDS on Salary (avg)",          value: "10–30%",            note: "Slab rate per employee" },
  { label: "Employer PF Contribution",     value: "12% of basic",      note: "₹1,800 max if basic > ₹15,000" },
  { label: "Professional Tax (Karnataka)", value: "₹200/month",        note: "Paid by employee, deducted by employer" },
  { label: "GST on SaaS/Services",         value: "18%",               note: "B2B invoices — Input Tax Credit available" },
  { label: "Startup Tax Exemption (80-IAC)", value: "100% for 3 yrs", note: "If DPIIT recognised — apply before Mar 31" },
];

export default function BudgetPage() {
  const { openChat } = useAppStore();
  const [, setBudgetId] = useState<string | null>(null);
  const [variance, setVariance] = useState<BudgetVarianceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "compliance" | "variance">("overview");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const budgets = await api.getBudgets();
        const first = budgets?.[0];
        if (first?.id) {
          setBudgetId(String(first.id));
          setVariance(await api.getBudgetVariance(String(first.id)));
        }
      } catch {
        // silently fall back to static FY data
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const chartVariance = useMemo(() =>
    (variance?.variances || []).slice(0, 8).map((v) => ({
      category: v.category,
      variance: v.variance,
    })),
  [variance]);

  const totalVariance = (variance?.variances || []).reduce((s, v) => s + v.variance, 0);
  const ytdSpend = MONTHLY_PROJECTION.filter((m) => m.actual).reduce((s, m) => s + (m.actual ?? 0), 0);

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-16 text-[#1d1b17]">
      <TopBar title="FY Budget & Planning" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* ── Hero ── */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.10)] sm:p-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Calculator className="h-3.5 w-3.5" />
                India Financial Year · Apr 2025 – Mar 2026
              </p>
              <h1 className="mt-3 text-3xl font-bold text-[#2c2013]">Annual Budget Plan</h1>
              <p className="mt-1 text-sm text-[#6b5948]">
                FY 2025-26 budget, compliance calendar, and variance tracking across all projects and departments
              </p>
              <div className="mt-4 flex flex-wrap gap-5">
                {[
                  { label: "Total Annual Budget",  value: INR(TOTAL_ANNUAL_BUDGET), color: "#1d4ed8" },
                  { label: "YTD Spend (Apr–Sep)",  value: INR(ytdSpend),            color: "#dc2626" },
                  { label: "Remaining (Oct–Mar)",  value: INR(TOTAL_ANNUAL_BUDGET - ytdSpend), color: "#15803d" },
                  { label: "Budget Period",         value: "FY 2025-26",             color: "#7c3aed" },
                ].map(({ label, value, color }) => (
                  <div key={label}>
                    <p className="text-[9px] font-black uppercase tracking-widest text-[#9c8872]">{label}</p>
                    <p className="text-base font-black" style={{ color }}>{value}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <button
                onClick={() => openChat("Analyze our FY 2025-26 budget — are we on track? Which categories are over-spending and how does it impact runway?")}
                className="inline-flex items-center gap-2 rounded-xl bg-[#1f1a16] px-4 py-2.5 text-xs font-bold text-[#fff6ea] hover:bg-[#14110f] transition-all"
              >
                <Sparkles className="h-3.5 w-3.5 text-amber-300" />
                Ask Finley
              </button>
              <button
                onClick={() => openChat("Calculate our advance tax liability for FY 2025-26 and tell me the next payment deadline")}
                className="inline-flex items-center gap-2 rounded-xl border border-[#d9c9b4] bg-white px-4 py-2.5 text-xs font-bold text-[#5f4c38] hover:bg-[#fdf6eb] transition-all"
              >
                <Scale className="h-3.5 w-3.5" />
                Calculate advance tax
              </button>
            </div>
          </div>
        </section>

        {/* ── Tabs ── */}
        <div className="flex gap-2">
          {(["overview", "compliance", "variance"] as const).map((tab) => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`rounded-xl px-4 py-2 text-xs font-bold capitalize transition-all ${
                activeTab === tab ? "bg-[#1f1a16] text-[#fff6ea]" : "bg-white border border-[#e0d4c6] text-[#6b5948] hover:bg-[#fdf6eb]"
              }`}>
              {tab === "overview" ? "Budget Overview" : tab === "compliance" ? "Tax & Compliance" : "Variance Analysis"}
            </button>
          ))}
        </div>

        {/* ── OVERVIEW TAB ── */}
        {activeTab === "overview" && (
          <div className="space-y-5">
            {/* Project budget allocation */}
            <section className="rounded-3xl border border-[#d9cdbc] bg-white p-6 shadow-[0_4px_24px_rgba(63,45,24,0.06)]">
              <h2 className="mb-4 text-base font-bold text-[#1d1b17]">Budget Allocation by Project (FY 2025-26)</h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {PROJECT_BUDGETS.map((p) => {
                  const monthly = p.annual / 12;
                  const ytd = monthly * 6 * (0.9 + Math.random() * 0.15);
                  const util = Math.round(ytd / (p.annual * 0.5) * 100);
                  return (
                    <div key={p.id} className="rounded-2xl border border-[#ede5d9] bg-[#faf7f3] p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-black" style={{ color: p.color }}>{p.name}</span>
                        <span className="text-[9px] font-bold text-[#9c8c7c]">{p.headcount} HC</span>
                      </div>
                      <p className="text-lg font-black text-[#1d1b17]">{INR(p.annual)}</p>
                      <p className="text-[9px] text-[#9c8c7c] mb-2">Annual · {INR(monthly)}/mo</p>
                      <div className="h-1.5 w-full rounded-full bg-[#ede5d9] overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${Math.min(util, 100)}%`, background: p.color }} />
                      </div>
                      <p className="mt-1 text-[9px] text-[#9c8c7c]">YTD utilisation ~{util}%</p>
                    </div>
                  );
                })}
              </div>
            </section>

            {/* Category budget bar chart */}
            <section className="rounded-3xl border border-[#d9cdbc] bg-white p-6 shadow-[0_4px_24px_rgba(63,45,24,0.06)]">
              <h2 className="mb-4 text-base font-bold text-[#1d1b17]">Annual Budget by Cost Category</h2>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={CATEGORY_BUDGETS} layout="vertical" barSize={18}>
                  <XAxis type="number" tickFormatter={(v) => INR(v)} tick={{ fontSize: 9, fill: "#9c8c7c" }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="category" tick={{ fontSize: 10, fill: "#6b5948" }} axisLine={false} tickLine={false} width={140} />
                  <Tooltip formatter={(v: number) => [INR(v), "Annual Budget"]} contentStyle={{ borderRadius: 10, border: "1px solid #e0d4c6", fontSize: 11 }} />
                  <Bar dataKey="budgeted" radius={[0, 6, 6, 0]}>
                    {CATEGORY_BUDGETS.map((c, i) => <Cell key={i} fill={c.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </section>

            {/* Monthly budget vs actual trend */}
            <section className="rounded-3xl border border-[#d9cdbc] bg-white p-6 shadow-[0_4px_24px_rgba(63,45,24,0.06)]">
              <h2 className="mb-1 text-base font-bold text-[#1d1b17]">Monthly Budget Tracking</h2>
              <p className="mb-4 text-xs text-[#9c8c7c]">Apr 2025 – Mar 2026 · Actuals through Sep, forecast from Oct</p>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={MONTHLY_PROJECTION}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0e8dc" vertical={false} />
                  <XAxis dataKey="month" tick={{ fontSize: 9, fill: "#9c8c7c" }} axisLine={false} tickLine={false} />
                  <YAxis tickFormatter={(v) => INR(v)} tick={{ fontSize: 9, fill: "#9c8c7c" }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: number, k: string) => [INR(v), k === "budget" ? "Budget" : k === "actual" ? "Actual" : "Forecast"]}
                    contentStyle={{ borderRadius: 10, border: "1px solid #e0d4c6", fontSize: 11 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="budget"   stroke="#b08a5c" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Budget" />
                  <Line type="monotone" dataKey="actual"   stroke="#dc2626" strokeWidth={2.5} dot={{ r: 3, fill: "#dc2626" }} name="Actual" connectNulls />
                  <Line type="monotone" dataKey="forecast" stroke="#6366f1" strokeWidth={2} strokeDasharray="4 2" dot={false} name="Forecast" connectNulls />
                </LineChart>
              </ResponsiveContainer>
            </section>
          </div>
        )}

        {/* ── COMPLIANCE TAB ── */}
        {activeTab === "compliance" && (
          <div className="space-y-5">
            {/* FY Calendar */}
            <section className="rounded-3xl border border-[#d9cdbc] bg-white p-6 shadow-[0_4px_24px_rgba(63,45,24,0.06)]">
              <div className="mb-4 flex items-center gap-2">
                <Calendar className="h-4.5 w-4.5 text-[#b08a5c]" />
                <h2 className="text-base font-bold text-[#1d1b17]">India Tax & Compliance Calendar — FY 2025-26</h2>
              </div>
              <div className="space-y-2">
                {TAX_DEADLINES.map((d, i) => {
                  const isPast  = new Date(d.date) < new Date("2026-04-22");
                  const isNear  = !isPast && new Date(d.date) < new Date("2026-06-01");
                  return (
                    <div key={i}
                      className={`flex items-start gap-3 rounded-2xl border px-4 py-3 ${
                        isPast  ? "border-[#dcfce7] bg-[#f0fdf4]"
                        : isNear ? "border-[#fde68a] bg-[#fffbeb]"
                        : "border-[#e5d9c8] bg-[#faf7f3]"
                      }`}>
                      <span className="text-base mt-0.5">{d.icon}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[10px] font-black uppercase tracking-wider text-[#9c8c7c]">{d.date}</span>
                          {isPast  && <span className="rounded-full bg-[#dcfce7] px-1.5 py-0.5 text-[9px] font-black text-[#15803d]">Done</span>}
                          {isNear  && <span className="rounded-full bg-[#fef3c7] px-1.5 py-0.5 text-[9px] font-black text-[#92400e]">Upcoming</span>}
                          <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-bold ${
                            d.type === "tax" ? "bg-[#fee2e2] text-[#991b1b]" : d.type === "milestone" ? "bg-[#ede9fe] text-[#5b21b6]" : "bg-[#dbeafe] text-[#1e40af]"
                          }`}>{d.type}</span>
                        </div>
                        <p className="text-sm font-semibold text-[#1d1b17]">{d.label}</p>
                      </div>
                      {!isPast && (
                        <button
                          onClick={() => openChat(`Tell me about the ${d.label} deadline and what we need to prepare`)}
                          className="shrink-0 text-[10px] text-[#b08a5c] hover:text-[#7a5c34] font-semibold transition-colors"
                        >
                          Ask Finley →
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>

            {/* Statutory Rules */}
            <section className="rounded-3xl border border-[#d9cdbc] bg-white p-6 shadow-[0_4px_24px_rgba(63,45,24,0.06)]">
              <div className="mb-4 flex items-center gap-2">
                <Scale className="h-4.5 w-4.5 text-[#b08a5c]" />
                <h2 className="text-base font-bold text-[#1d1b17]">India Statutory Rates Applied (FY 2025-26)</h2>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {COMPLIANCE_RULES.map((r) => (
                  <div key={r.label} className="rounded-2xl bg-[#faf7f3] border border-[#ede5d9] px-4 py-3">
                    <p className="text-[9px] font-black uppercase tracking-widest text-[#9c8c7c]">{r.label}</p>
                    <p className="text-base font-black text-[#1d1b17] mt-0.5">{r.value}</p>
                    <p className="text-[10px] text-[#b08a5c] mt-1">{r.note}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* Advance tax calculator prompt */}
            <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(135deg,#1f1a16,#2e231a)] p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs font-black text-amber-400 uppercase tracking-wider">Finley · Tax Intelligence</p>
                  <p className="mt-1 text-sm font-bold text-white">Let Finley calculate your exact tax liability</p>
                  <p className="text-xs text-[#c8b89e] mt-0.5">Based on YTD P&L, projected FY income, and applicable deductions</p>
                </div>
                <div className="flex flex-col gap-2">
                  {["Calculate Q3 advance tax instalment", "Check 80-IAC startup exemption eligibility", "Optimise deductions under Section 37(1)"].map((q) => (
                    <button key={q} onClick={() => openChat(q)}
                      className="rounded-xl border border-[#4a3c2e] bg-[#2e2419]/60 px-3 py-1.5 text-left text-[11px] text-[#e8d9c6] hover:bg-[#3d3025]/60 hover:text-white transition-all">
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </section>
          </div>
        )}

        {/* ── VARIANCE TAB ── */}
        {activeTab === "variance" && (
          <div className="space-y-5">
            {loading && (
              <div className="flex items-center gap-2 rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-4 text-sm text-[#6f5f4b]">
                <RefreshCw className="h-4 w-4 animate-spin" />
                Loading live variance data…
              </div>
            )}

            {chartVariance.length > 0 ? (
              <>
                <div className="grid gap-4 sm:grid-cols-3">
                  {[
                    { label: "Budget name",    value: variance?.budget_name || "FY 2025-26", icon: BarChart3 },
                    { label: "Total variance", value: formatCurrency(totalVariance),          icon: totalVariance >= 0 ? TrendingUp : TrendingDown },
                    { label: "Categories",     value: String(chartVariance.length),           icon: Calculator },
                  ].map(({ label, value, icon: Icon }) => (
                    <article key={label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-4">
                      <div className="flex items-center justify-between">
                        <p className="text-[10px] uppercase tracking-widest text-[#9c8c7c]">{label}</p>
                        <Icon className="h-4 w-4 text-[#87602a]" />
                      </div>
                      <p className="mt-2 text-xl font-black text-[#2a2017]">{value}</p>
                    </article>
                  ))}
                </div>

                <section className="grid gap-4 lg:grid-cols-2">
                  <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
                    <h2 className="mb-4 text-base font-bold text-[#2a2017]">Variance by Category</h2>
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={chartVariance} layout="vertical">
                        <XAxis type="number" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 10 }} />
                        <YAxis type="category" dataKey="category" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 10 }} width={120} />
                        <Tooltip contentStyle={{ border: "1px solid #dbcdb9", borderRadius: 12, background: "#fff8ea" }} formatter={(v: number) => formatCurrency(v)} />
                        <Bar dataKey="variance" radius={[0, 8, 8, 0]}>
                          {chartVariance.map((c, i) => <Cell key={i} fill={c.variance >= 0 ? "#dc2626" : "#15803d"} />)}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </article>

                  <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
                    <h2 className="mb-4 text-base font-bold text-[#2a2017]">Line-by-line Breakdown</h2>
                    <div className="space-y-2">
                      {(variance?.variances || []).map((item) => (
                        <div key={item.category} className="rounded-xl border border-[#e8dcc9] bg-[#fff8ec] px-4 py-3 text-sm">
                          <div className="flex items-center justify-between gap-4">
                            <div>
                              <p className="font-semibold text-[#2a2017]">{item.category}</p>
                              <p className="text-xs text-[#7b6d5b]">Budget {formatCurrency(item.budget)} vs actual {formatCurrency(item.actual)}</p>
                            </div>
                            <span className={cn("font-black", item.variance >= 0 ? "text-[#dc2626]" : "text-[#15803d]")}>
                              {item.variance >= 0 ? "+" : ""}{formatCurrency(item.variance)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </article>
                </section>
              </>
            ) : !loading ? (
              <div className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-6 text-center">
                <Info className="mx-auto h-8 w-8 text-[#b08a5c] mb-2" />
                <p className="text-sm font-semibold text-[#6f5f4b]">No variance data in the live database yet.</p>
                <p className="text-xs text-[#9c8c7c] mt-1">The overview and compliance tabs show the full FY 2025-26 plan.</p>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
