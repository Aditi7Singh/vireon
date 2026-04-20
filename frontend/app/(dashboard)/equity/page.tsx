"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import {
  DollarSign, Sparkles, TrendingUp, Users, PieChart, Plus,
  Calendar, FileText, ChevronRight, Building2, Shield,
} from "lucide-react";
import { PieChart as RechartsPie, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const CAP_TABLE = [
  { name: "Aditi Singh (Founder)", type: "Common", shares: 3500000, pct: 35.0, series: "Founder" },
  { name: "Rahul Mehta (Co-Founder)", type: "Common", shares: 2500000, pct: 25.0, series: "Founder" },
  { name: "Sequoia Capital", type: "Preferred", shares: 1500000, pct: 15.0, series: "Series A" },
  { name: "Y Combinator", type: "Preferred", shares: 500000, pct: 5.0, series: "Seed" },
  { name: "Pioneer Fund", type: "Preferred", shares: 750000, pct: 7.5, series: "Series A" },
  { name: "Uncorrelated VC", type: "Preferred", shares: 250000, pct: 2.5, series: "Seed" },
  { name: "Employee Stock Pool (ESOP)", type: "Options", shares: 900000, pct: 9.0, series: "ESOP" },
  { name: "Advisors", type: "Options", shares: 100000, pct: 1.0, series: "ESOP" },
];

const FUNDING_ROUNDS = [
  { round: "Pre-Seed", date: "Jan 2024", amount: 500000, valuation: 5000000, investors: ["Friends & Family", "Founder capital"], dilution: 10, lead: "Self" },
  { round: "Seed", date: "Jun 2024", amount: 2000000, valuation: 12000000, investors: ["Y Combinator", "Uncorrelated VC"], dilution: 16.7, lead: "Y Combinator" },
  { round: "Series A", date: "Jan 2026", amount: 12000000, valuation: 58000000, investors: ["Sequoia Capital", "Pioneer Fund"], dilution: 22.5, lead: "Sequoia" },
];

const COLORS = ["#2c2520", "#8d4f27", "#b3622d", "#d4956a", "#e8c4a0", "#f0d8c0", "#f6ebe0", "#faf5ee"];

const SCENARIO_COLS = [
  { label: "Conservative", exitVal: 150000000, multiple: 2.6 },
  { label: "Base Case", exitVal: 300000000, multiple: 5.2 },
  { label: "Optimistic", exitVal: 600000000, multiple: 10.3 },
  { label: "Grand Slam", exitVal: 1200000000, multiple: 20.7 },
];

export default function EquityPage() {
  const { openChat } = useAppStore();
  const [activeTab, setActiveTab] = useState<"captable" | "rounds" | "scenarios">("captable");
  const [dilutionShares, setDilutionShares] = useState(1000000);

  const totalShares = CAP_TABLE.reduce((s, r) => s + r.shares, 0);
  const currentValuation = FUNDING_ROUNDS[FUNDING_ROUNDS.length - 1].valuation;
  const totalRaised = FUNDING_ROUNDS.reduce((s, r) => s + r.amount, 0);
  const founderPct = CAP_TABLE.filter(r => r.series === "Founder").reduce((s, r) => s + r.pct, 0);

  const postDilutionPct = (founderPct / 100) * (totalShares / (totalShares + dilutionShares)) * 100;

  const pieData = CAP_TABLE.map(r => ({ name: r.name.split(" (")[0].split(" ").slice(0, 2).join(" "), value: r.pct }));

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Equity & Cap Table" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <PieChart className="h-3.5 w-3.5" /> Equity Intelligence
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Cap Table & Fundraising</h1>
              <p className="mt-1 text-sm text-[#5f5344]">Track ownership, model dilution, and plan future fundraising scenarios.</p>
            </div>
            <button onClick={() => openChat("When should we raise our Series B and at what valuation target?")} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white self-start lg:self-auto">
              <Sparkles className="h-4 w-4" /> Fundraising Advice
            </button>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Post-Money Valuation", value: formatCurrency(currentValuation), sub: "Series A · Jan 2026" },
            { label: "Total Raised", value: formatCurrency(totalRaised), sub: "3 rounds" },
            { label: "Founder Ownership", value: `${founderPct.toFixed(1)}%`, sub: "Combined equity" },
            { label: "Total Shares", value: (totalShares / 1000000).toFixed(1) + "M", sub: "Outstanding" },
          ].map(s => (
            <article key={s.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{s.label}</p>
              <p className="mt-2 text-2xl font-bold text-[#2a2017]">{s.value}</p>
              <p className="mt-1 text-xs text-[#9a8872]">{s.sub}</p>
            </article>
          ))}
        </section>

        {/* Tabs */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="flex gap-1 bg-[#f0ebe3] p-1 m-5 rounded-xl w-fit">
            {([["captable", "Cap Table"], ["rounds", "Funding Rounds"], ["scenarios", "Exit Scenarios"]] as const).map(([key, label]) => (
              <button key={key} onClick={() => setActiveTab(key)} className={cn("rounded-lg px-4 py-2 text-xs font-bold transition-all", activeTab === key ? "bg-white text-[#2a2017] shadow-sm" : "text-[#776b5a] hover:text-[#2a2017]")}>
                {label}
              </button>
            ))}
          </div>

          <div className="px-5 pb-6">
            {activeTab === "captable" && (
              <div className="grid gap-6 lg:grid-cols-2">
                <div>
                  <h3 className="text-base font-bold text-[#2a2017] mb-4">Ownership Distribution</h3>
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsPie>
                        <Pie data={pieData} cx="50%" cy="50%" outerRadius={110} dataKey="value" label={({ name, value }) => `${name}: ${value}%`} labelLine={false}>
                          {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                        </Pie>
                        <Tooltip formatter={(v: number) => [`${v}%`]} />
                      </RechartsPie>
                    </ResponsiveContainer>
                  </div>
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#2a2017] mb-4">Shareholder Register</h3>
                  <div className="space-y-2">
                    {CAP_TABLE.map((row) => (
                      <div key={row.name} className="flex items-center justify-between py-2 border-b border-[#f0ebe3]">
                        <div>
                          <p className="text-sm font-semibold text-[#2a2017]">{row.name}</p>
                          <p className="text-xs text-[#9a8872]">{row.type} · {row.series}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-bold text-[#2a2017]">{row.pct.toFixed(1)}%</p>
                          <p className="text-xs text-[#9a8872]">{(row.shares / 1000).toFixed(0)}K shares</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === "rounds" && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-[#2a2017]">Funding History</h3>
                {FUNDING_ROUNDS.map((round, i) => (
                  <div key={round.round} className="rounded-xl border border-[#ede8e0] p-5">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <span className="inline-block rounded-full px-2.5 py-0.5 text-xs font-bold mb-2" style={{ background: COLORS[i * 2], color: "white" }}>{round.round}</span>
                        <p className="text-lg font-bold text-[#2a2017]">{formatCurrency(round.amount)} raised</p>
                        <p className="text-sm text-[#776b5a]">{round.date} · Lead: {round.lead}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-[#776b5a]">Post-money</p>
                        <p className="text-xl font-black text-[#2a2017]">{formatCurrency(round.valuation)}</p>
                        <p className="text-xs text-red-600">−{round.dilution}% dilution</p>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {round.investors.map(inv => (
                        <span key={inv} className="rounded-full bg-[#f0ebe3] border border-[#ddd2c2] text-xs font-medium text-[#5f5344] px-3 py-1">{inv}</span>
                      ))}
                    </div>
                  </div>
                ))}
                <div className="rounded-xl border-2 border-dashed border-[#ddd2c2] p-5 text-center">
                  <p className="text-sm font-bold text-[#776b5a] mb-2">Series B · Planned Q1 2027</p>
                  <p className="text-xs text-[#9a8872] mb-3">Target: $35–50M at $180–220M valuation</p>
                  <button onClick={() => openChat("Model our Series B fundraise at $200M valuation")} className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                    <Sparkles className="h-4 w-4" /> Model Series B
                  </button>
                </div>
              </div>
            )}

            {activeTab === "scenarios" && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-base font-bold text-[#2a2017] mb-1">Exit Scenario Analysis</h3>
                  <p className="text-xs text-[#776b5a] mb-4">Founder proceeds at various exit valuations, post all liquidation preferences.</p>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    {SCENARIO_COLS.map((s, i) => {
                      const founderProceeds = s.exitVal * (founderPct / 100) * 0.82; // approx after preferences
                      return (
                        <div key={s.label} className={cn("rounded-xl border p-4", i === 1 ? "border-[#b3622d] bg-[#fff8f0]" : "border-[#ede8e0] bg-[#fafaf8]")}>
                          {i === 1 && <span className="text-xs font-black text-[#8d4f27] uppercase tracking-wide">Base Case</span>}
                          <p className="text-sm font-bold text-[#2a2017] mt-1">{s.label}</p>
                          <p className="text-xs text-[#776b5a]">Exit: {formatCurrency(s.exitVal)}</p>
                          <p className="text-2xl font-black text-[#2a2017] mt-3">{formatCurrency(founderProceeds)}</p>
                          <p className="text-xs text-[#9a8872]">Founder proceeds ({founderPct}%)</p>
                          <p className="text-xs text-emerald-600 font-semibold mt-1">{s.multiple}x · {(s.exitVal / totalRaised).toFixed(1)}x MOIC</p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="rounded-xl border border-[#ede8e0] p-5">
                  <h3 className="text-sm font-bold text-[#2a2017] mb-3">Dilution Modeler — Next Round</h3>
                  <div className="flex items-center gap-4 flex-wrap">
                    <div>
                      <label className="text-xs text-[#776b5a]">New shares to issue</label>
                      <input type="range" min={500000} max={3000000} step={100000} value={dilutionShares} onChange={e => setDilutionShares(Number(e.target.value))} className="block mt-1 w-48" />
                      <p className="text-xs text-[#9a8872]">{(dilutionShares / 1000000).toFixed(2)}M shares</p>
                    </div>
                    <div className="rounded-xl bg-[#f9f6f1] border border-[#ede8e0] p-4">
                      <p className="text-xs text-[#776b5a]">Post-dilution founder ownership</p>
                      <p className="text-2xl font-black text-[#2a2017]">{postDilutionPct.toFixed(1)}%</p>
                      <p className="text-xs text-red-500">from {founderPct.toFixed(1)}% (−{(founderPct - postDilutionPct).toFixed(1)}pp)</p>
                    </div>
                    <div className="rounded-xl bg-[#f9f6f1] border border-[#ede8e0] p-4">
                      <p className="text-xs text-[#776b5a]">Implied dilution %</p>
                      <p className="text-2xl font-black text-amber-700">{((dilutionShares / (totalShares + dilutionShares)) * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
