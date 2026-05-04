"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import { API_V1_BASE } from "@/lib/api";
import {
  TrendingUp, TrendingDown, Users, Flame, Target, MapPin,
  Sparkles, RefreshCw, ChevronRight, BarChart3, Zap,
  FlaskConical, Leaf, Building2,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Legend, CartesianGrid,
} from "recharts";

const INR = (n: number) =>
  n >= 10_000_000
    ? `₹${(n / 10_000_000).toFixed(2)}Cr`
    : n >= 100_000
    ? `₹${(n / 100_000).toFixed(1)}L`
    : `₹${n.toLocaleString("en-IN")}`;

const PROJECT_ICONS: Record<string, React.ElementType> = {
  sprouts: Leaf,
  orchard: Building2,
  ai_lab:  FlaskConical,
};

const STATUS_META: Record<string, { label: string; bg: string; text: string }> = {
  on_track:    { label: "On Track",    bg: "#dcfce7", text: "#15803d" },
  at_risk:     { label: "At Risk",     bg: "#fef9c3", text: "#a16207" },
  over_budget: { label: "Over Budget", bg: "#fee2e2", text: "#b91c1c" },
};

const STAGE_META: Record<string, { bg: string; text: string }> = {
  green:  { bg: "#dcfce7", text: "#15803d" },
  orange: { bg: "#ffedd5", text: "#c2410c" },
  purple: { bg: "#ede9fe", text: "#6d28d9" },
};

interface ProjectData {
  id: string;
  name: string;
  tagline: string;
  stage: string;
  stage_color: string;
  location: string;
  color: string;
  accent: string;
  revenue_inr: number;
  payroll_inr: number;
  infra_inr: number;
  other_costs_inr: number;
  burn_inr: number;
  net_inr: number;
  headcount: number;
  headcount_target: number;
  budget_annual_inr: number;
  budget_monthly_inr: number;
  budget_utilization_pct: number;
  arr_target_inr: number;
  arr_attainment_pct: number;
  status: string;
}

interface Overview {
  company: string;
  fiscal_year: string;
  as_of: string;
  projects: ProjectData[];
  totals: { revenue_inr: number; burn_inr: number; net_inr: number; headcount: number };
}

interface TrendRow {
  month: string;
  [key: string]: number | string;
}

export default function ProjectsPage() {
  const { openChat } = useAppStore();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [trend, setTrend] = useState<TrendRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeProject, setActiveProject] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [ov, tr] = await Promise.all([
        fetch(`${API_V1_BASE}/projects/overview`, {
          headers: { Authorization: `Bearer ${localStorage.getItem("access_token") || localStorage.getItem("auth_token")}` },
        }).then((r) => r.json()),
        fetch(`${API_V1_BASE}/projects/monthly-trend`, {
          headers: { Authorization: `Bearer ${localStorage.getItem("access_token") || localStorage.getItem("auth_token")}` },
        }).then((r) => r.json()),
      ]);
      setOverview(ov);
      setTrend(tr.trend || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const projects = overview?.projects ?? [];
  const totals   = overview?.totals;
  const shown    = activeProject ? projects.filter((p) => p.id === activeProject) : projects;

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-16 text-[#1d1b17]">
      <TopBar title="Project Portfolio" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* ── Hero Banner ── */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.10)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Zap className="h-3.5 w-3.5" />
                Vireon Seeding Lab · FY 2025-26
              </p>
              <h1 className="mt-3 text-3xl font-bold text-[#2c2013]">Portfolio Overview</h1>
              <p className="mt-1 text-sm text-[#6b5948]">
                {overview?.fiscal_year ?? "FY 2025-26 (Apr 2025 – Mar 2026)"} · Three active projects across Sprout, Orchard & AI Lab
              </p>

              {totals && (
                <div className="mt-4 flex flex-wrap gap-6">
                  {[
                    { label: "Total Revenue",  value: INR(totals.revenue_inr), icon: TrendingUp,  color: "#15803d" },
                    { label: "Total Burn",     value: INR(totals.burn_inr),    icon: Flame,        color: "#b91c1c" },
                    { label: "Net Cash Flow",  value: INR(totals.net_inr),     icon: totals.net_inr >= 0 ? TrendingUp : TrendingDown, color: totals.net_inr >= 0 ? "#15803d" : "#b91c1c" },
                    { label: "Total Headcount",value: String(totals.headcount), icon: Users,       color: "#1d4ed8" },
                  ].map(({ label, value, icon: Icon, color }) => (
                    <div key={label} className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-xl" style={{ background: color + "20" }}>
                        <Icon className="h-4 w-4" style={{ color }} />
                      </div>
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-[#9c8872]">{label}</p>
                        <p className="text-lg font-black text-[#1d1b17]">{value}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-2 lg:flex-col lg:items-end">
              <button
                onClick={() => openChat("Show me the overall portfolio health for Sprout, Orchard and AI Lab — revenue, burn, runway impact")}
                className="inline-flex items-center gap-2 rounded-xl bg-[#1f1a16] px-4 py-2.5 text-xs font-bold text-[#fff6ea] hover:bg-[#14110f] active:scale-95 transition-all"
              >
                <Sparkles className="h-3.5 w-3.5 text-amber-300" />
                Ask Finley about portfolio
              </button>
              <button
                onClick={load}
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-xl border border-[#d9c9b4] bg-white px-4 py-2.5 text-xs font-bold text-[#5f4c38] hover:bg-[#fdf6eb] transition-all"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </button>
            </div>
          </div>
        </section>

        {/* ── Filter tabs ── */}
        <div className="flex gap-2">
          {[null, ...projects.map((p) => p.id)].map((id) => (
            <button
              key={id ?? "all"}
              onClick={() => setActiveProject(id)}
              className={`rounded-xl px-3 py-1.5 text-xs font-bold transition-all ${
                activeProject === id
                  ? "bg-[#1f1a16] text-[#fff6ea]"
                  : "bg-white border border-[#e0d4c6] text-[#6b5948] hover:bg-[#fdf6eb]"
              }`}
            >
              {id ? projects.find((p) => p.id === id)?.name : "All Projects"}
            </button>
          ))}
        </div>

        {/* ── Project Cards ── */}
        {loading ? (
          <div className="grid gap-4 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-72 animate-pulse rounded-3xl bg-[#ede5d8]" />
            ))}
          </div>
        ) : (
          <div className={`grid gap-5 ${shown.length === 1 ? "lg:grid-cols-1 max-w-xl" : shown.length === 2 ? "lg:grid-cols-2" : "lg:grid-cols-3"}`}>
            {shown.map((p) => {
              const Icon      = PROJECT_ICONS[p.id] ?? Leaf;
              const stageMeta = STAGE_META[p.stage_color] ?? STAGE_META.green;
              const statusMeta= STATUS_META[p.status] ?? STATUS_META.on_track;

              return (
                <div
                  key={p.id}
                  className="rounded-3xl border border-[#ddd0be] bg-white shadow-[0_8px_32px_rgba(63,45,24,0.07)] overflow-hidden flex flex-col hover:shadow-[0_16px_48px_rgba(63,45,24,0.12)] transition-shadow"
                >
                  {/* Header strip */}
                  <div className="h-2 w-full" style={{ background: p.color }} />

                  <div className="flex flex-col gap-4 p-5 flex-1">
                    {/* Title row */}
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl" style={{ background: p.color + "18" }}>
                          <Icon className="h-5 w-5" style={{ color: p.color }} />
                        </div>
                        <div>
                          <h2 className="text-base font-black text-[#1d1b17]">{p.name}</h2>
                          <p className="flex items-center gap-1 text-[10px] text-[#8b7a69]">
                            <MapPin className="h-2.5 w-2.5" />
                            {p.location}
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1.5">
                        <span className="rounded-full px-2 py-0.5 text-[10px] font-black uppercase tracking-wider"
                          style={{ background: stageMeta.bg, color: stageMeta.text }}>
                          {p.stage}
                        </span>
                        <span className="rounded-full px-2 py-0.5 text-[10px] font-bold"
                          style={{ background: statusMeta.bg, color: statusMeta.text }}>
                          {statusMeta.label}
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-[#7a6a59] leading-relaxed">{p.tagline}</p>

                    {/* Key metrics grid */}
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { label: "Monthly Revenue", value: INR(p.revenue_inr), color: "#15803d" },
                        { label: "Monthly Burn",    value: INR(p.burn_inr),    color: "#dc2626" },
                        { label: "Net Cash",        value: INR(p.net_inr),     color: p.net_inr >= 0 ? "#15803d" : "#dc2626" },
                        { label: "Headcount",       value: `${p.headcount} / ${p.headcount_target}`, color: "#1d4ed8" },
                      ].map(({ label, value, color }) => (
                        <div key={label} className="rounded-2xl bg-[#faf7f3] px-3 py-2.5 border border-[#ede5d9]">
                          <p className="text-[9px] font-black uppercase tracking-widest text-[#9c8c7c]">{label}</p>
                          <p className="mt-0.5 text-sm font-black" style={{ color }}>{value}</p>
                        </div>
                      ))}
                    </div>

                    {/* Cost breakdown */}
                    <div className="space-y-1.5">
                      <p className="text-[9px] font-black uppercase tracking-widest text-[#9c8c7c]">Cost Structure</p>
                      {[
                        { label: "Salaries", amount: p.payroll_inr, color: "#f59e0b" },
                        { label: "Cloud / Infra", amount: p.infra_inr, color: "#6366f1" },
                        { label: "Other OpEx", amount: p.other_costs_inr, color: "#ec4899" },
                      ].map(({ label, amount, color }) => (
                        <div key={label} className="flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: color }} />
                          <span className="flex-1 text-xs text-[#6b5948]">{label}</span>
                          <span className="text-xs font-bold text-[#1d1b17]">{INR(amount)}</span>
                        </div>
                      ))}
                    </div>

                    {/* Budget utilization bar */}
                    <div>
                      <div className="flex justify-between text-[10px] mb-1">
                        <span className="font-bold text-[#7a6a59]">Budget utilization</span>
                        <span className="font-black" style={{ color: p.budget_utilization_pct > 100 ? "#dc2626" : p.budget_utilization_pct > 85 ? "#ca8a04" : "#15803d" }}>
                          {p.budget_utilization_pct}%
                        </span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-[#ede5d9] overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-700"
                          style={{
                            width: `${Math.min(p.budget_utilization_pct, 100)}%`,
                            background: p.budget_utilization_pct > 100 ? "#dc2626" : p.budget_utilization_pct > 85 ? "#f59e0b" : p.color,
                          }}
                        />
                      </div>
                      <p className="mt-1 text-[9px] text-[#9c8c7c]">Monthly budget: {INR(p.budget_monthly_inr)}</p>
                    </div>

                    {/* ARR attainment */}
                    <div className="mt-auto flex items-center justify-between rounded-2xl bg-[#f7f3ee] border border-[#e8dfd4] px-3 py-2">
                      <div>
                        <p className="text-[9px] font-black uppercase tracking-widest text-[#9c8c7c]">ARR Attainment</p>
                        <p className="text-xs font-black text-[#1d1b17]">
                          {INR(p.revenue_inr * 12)} / {INR(p.arr_target_inr)}
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <Target className="h-3.5 w-3.5 text-[#8b7a69]" />
                        <span className="text-sm font-black" style={{ color: p.color }}>{p.arr_attainment_pct}%</span>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-[#ede5d9] px-5 py-3">
                    <button
                      onClick={() => openChat(`Deep dive on the ${p.name} project — revenue trend, burn by category, and 3-month forecast`)}
                      className="flex w-full items-center justify-between text-xs font-bold text-[#8b5e27] hover:text-[#5f3d18] transition-colors"
                    >
                      <span>Ask Finley about {p.name}</span>
                      <ChevronRight className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── Revenue vs Burn Trend Chart ── */}
        {trend.length > 0 && (
          <section className="rounded-3xl border border-[#d9cdbc] bg-white p-6 shadow-[0_8px_32px_rgba(63,45,24,0.07)]">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-[#9c8c7c]">6-Month Trend</p>
                <h2 className="text-lg font-bold text-[#1d1b17]">Revenue vs Burn by Project</h2>
              </div>
              <BarChart3 className="h-5 w-5 text-[#b08a5c]" />
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={trend} barGap={2} barCategoryGap="28%">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0e8dc" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 10, fill: "#9c8c7c" }} axisLine={false} tickLine={false} />
                <YAxis tickFormatter={(v) => `₹${(v / 100000).toFixed(0)}L`} tick={{ fontSize: 10, fill: "#9c8c7c" }} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(val: number, name: string) => [INR(val), name.replace("_revenue", " Revenue").replace("_burn", " Burn").replace("sprouts", "Sprout").replace("orchard", "Orchard").replace("ai_lab", "AI Lab")]}
                  contentStyle={{ borderRadius: 12, border: "1px solid #e0d4c6", background: "#fffdf9", fontSize: 11 }}
                />
                <Legend formatter={(val) => val.replace("_revenue", " Rev").replace("_burn", " Burn").replace("sprouts", "Sprout").replace("orchard", "Orchard").replace("ai_lab", "AI Lab")} wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="sprouts_revenue" fill="#16a34a" radius={[4, 4, 0, 0]} />
                <Bar dataKey="orchard_revenue" fill="#ea580c" radius={[4, 4, 0, 0]} />
                <Bar dataKey="ai_lab_revenue"  fill="#7c3aed" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </section>
        )}

        {/* ── Finley context prompt ── */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(135deg,#1f1a16_0%,#2e231a_100%)] p-6 shadow-[0_8px_32px_rgba(0,0,0,0.18)]">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-black uppercase tracking-widest text-amber-400">Finley · AI CFO</p>
              <h3 className="mt-1 text-lg font-bold text-white">Get deeper portfolio intelligence</h3>
              <p className="mt-1 text-xs text-[#c8b89e]">
                Ask about cross-project runway impact, optimal budget reallocation, or hiring plans.
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:items-end">
              {[
                "Which project has the best unit economics?",
                "How does AI Lab burn impact our overall runway?",
                "Recommend optimal budget split for next quarter",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => openChat(q)}
                  className="rounded-xl border border-[#4a3c2e] bg-[#2e2419]/60 px-3 py-2 text-left text-xs text-[#e8d9c6] hover:bg-[#3d3025]/60 hover:text-white transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
