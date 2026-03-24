"use client";

import { useState, useEffect } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import api from "@/lib/api";
import { Sparkles, Briefcase, Globe, Target, Wallet, TrendingDown, TrendingUp } from "lucide-react";

type PlanningMode = "defensive" | "balanced" | "aggressive";
type CashPolicy = "preserve" | "growth";

const MODE_PRESETS: Record<PlanningMode, { hiringCount: number; salaryK: number; revenueShift: number; label: string; note: string }> = {
  defensive: {
    hiringCount: 2,
    salaryK: 85,
    revenueShift: -8,
    label: "Defensive",
    note: "Protect runway under demand softness.",
  },
  balanced: {
    hiringCount: 6,
    salaryK: 105,
    revenueShift: 10,
    label: "Balanced",
    note: "Stable hiring with moderate growth expectations.",
  },
  aggressive: {
    hiringCount: 12,
    salaryK: 135,
    revenueShift: 24,
    label: "Aggressive",
    note: "Push expansion and accept higher cash pressure.",
  },
};

export default function ScenariosPage() {
  const { openChat } = useAppStore();
  const [planningMode, setPlanningMode] = useState<PlanningMode>("balanced");
  const [cashPolicy, setCashPolicy] = useState<CashPolicy>("preserve");
  const [hiringSim, setHiringSim] = useState({ count: MODE_PRESETS.balanced.hiringCount, salary: MODE_PRESETS.balanced.salaryK });
  const [revenueShift, setRevenueShift] = useState(MODE_PRESETS.balanced.revenueShift);
  const [history, setHistory] = useState<any[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  const policyMultiplier = cashPolicy === "preserve" ? 0.85 : 1.2;
  const monthlyHiringBurden = (hiringSim.count * hiringSim.salary * 1000) / 12;
  const annualHiringBurden = monthlyHiringBurden * 12;

  const runwayDropMonths = (monthlyHiringBurden / 160000) * policyMultiplier;
  const revenueRunwayEffect = revenueShift / 3.4;
  const netRunwayEffect = revenueRunwayEffect - runwayDropMonths;
  const operatingSignal = netRunwayEffect < -1.5 ? "high-risk" : netRunwayEffect < 0 ? "caution" : "healthy";

  const applyMode = (mode: PlanningMode) => {
    setPlanningMode(mode);
    setHiringSim({
      count: MODE_PRESETS[mode].hiringCount,
      salary: MODE_PRESETS[mode].salaryK,
    });
    setRevenueShift(MODE_PRESETS[mode].revenueShift);
  };

  const fetchHistory = async () => {
    try {
      const data = await api.getScenarioHistory();
      setHistory(data || []);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { void fetchHistory(); }, []);

  const saveScenario = async (type: string, data: any, result: any) => {
    setIsSaving(true);
    try {
      await api.saveScenario({
        name: `${type} Plan - ${new Date().toLocaleDateString()}`,
        scenario_type: type,
        input_data: data,
        result_data: result,
      });
      fetchHistory();
    } catch (e) { console.error(e); }
    finally { setIsSaving(false); }
  };

  const recommendationText =
    operatingSignal === "high-risk"
      ? "Runway compression is severe. Delay non-critical hiring or pair this plan with immediate cost controls."
      : operatingSignal === "caution"
        ? "Plan is viable with control gates. Track monthly burn and tie hiring releases to revenue milestones."
        : "Runway impact is acceptable. This plan supports growth with manageable cash pressure.";

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Strategic Simulations" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Target className="h-3.5 w-3.5" />
                Scenario engine
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Plan decisions before they cost you</h1>
              <p className="mt-2 text-sm text-[#5f5344]">Choose finance modes, apply cash policy, and test runway impact before committing budget.</p>
            </div>
            <button
              onClick={() => openChat("Build an executive scenario memo with assumptions, runway impact, risks, and recommended controls.")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
            >
              <Sparkles className="h-4 w-4" />
              Generate executive memo
            </button>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#7a6a54]">Planning Mode</p>
              <div className="mt-2 inline-flex w-full rounded-xl border border-[#dbc9ac] bg-[#fff8ea] p-1">
                {(["defensive", "balanced", "aggressive"] as PlanningMode[]).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => applyMode(mode)}
                    className={`flex-1 rounded-lg px-3 py-2 text-xs font-semibold transition ${
                      planningMode === mode ? "bg-[#2a2118] text-[#fff4e4]" : "text-[#5f503f] hover:bg-[#f2e7d6]"
                    }`}
                  >
                    {MODE_PRESETS[mode].label}
                  </button>
                ))}
              </div>
              <p className="mt-2 text-xs text-[#776653]">{MODE_PRESETS[planningMode].note}</p>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#7a6a54]">Cash Policy</p>
              <div className="mt-2 inline-flex w-full rounded-xl border border-[#dbc9ac] bg-[#fff8ea] p-1">
                <button
                  onClick={() => setCashPolicy("preserve")}
                  className={`flex-1 rounded-lg px-3 py-2 text-xs font-semibold transition ${
                    cashPolicy === "preserve" ? "bg-[#2a2118] text-[#fff4e4]" : "text-[#5f503f] hover:bg-[#f2e7d6]"
                  }`}
                >
                  Preserve Runway
                </button>
                <button
                  onClick={() => setCashPolicy("growth")}
                  className={`flex-1 rounded-lg px-3 py-2 text-xs font-semibold transition ${
                    cashPolicy === "growth" ? "bg-[#2a2118] text-[#fff4e4]" : "text-[#5f503f] hover:bg-[#f2e7d6]"
                  }`}
                >
                  Growth Push
                </button>
              </div>
              <p className="mt-2 text-xs text-[#776653]">Policy changes sensitivity so finance can compare conservative vs aggressive cash posture.</p>
            </div>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-4">
          <div className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-4">
            <p className="text-[11px] uppercase tracking-[0.12em] text-[#8c7b67]">Monthly Hiring Burden</p>
            <p className="mt-1 text-xl font-bold text-[#2e2417]">${monthlyHiringBurden.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
          </div>
          <div className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-4">
            <p className="text-[11px] uppercase tracking-[0.12em] text-[#8c7b67]">Annual Hiring Cost</p>
            <p className="mt-1 text-xl font-bold text-[#2e2417]">${annualHiringBurden.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
          </div>
          <div className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-4">
            <p className="text-[11px] uppercase tracking-[0.12em] text-[#8c7b67]">Revenue Effect</p>
            <p className={`mt-1 text-xl font-bold ${revenueRunwayEffect >= 0 ? "text-[#1f7a41]" : "text-[#b1462f]"}`}>{revenueRunwayEffect >= 0 ? "+" : ""}{revenueRunwayEffect.toFixed(1)} mo</p>
          </div>
          <div className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-4">
            <p className="text-[11px] uppercase tracking-[0.12em] text-[#8c7b67]">Net Runway Effect</p>
            <p className={`mt-1 text-xl font-bold ${netRunwayEffect >= 0 ? "text-[#1f7a41]" : "text-[#b1462f]"}`}>{netRunwayEffect >= 0 ? "+" : ""}{netRunwayEffect.toFixed(1)} mo</p>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-6">
            <div className="mb-4 flex items-center justify-between">
              <div className="inline-flex items-center gap-2 text-[#71562f] font-semibold"><Briefcase className="h-4 w-4" />Hiring Simulation</div>
              <button 
                onClick={() => saveScenario("hiring", { ...hiringSim, planningMode, cashPolicy }, { runway_drop_months: runwayDropMonths, monthly_hiring_burden: monthlyHiringBurden })}
                disabled={isSaving}
                className="text-xs text-[#8d4f27] font-bold hover:underline"
              >
                {isSaving ? "Saving..." : "Save Snapshot"}
              </button>
            </div>
            <label className="text-xs uppercase tracking-[0.12em] text-[#7b6d5b]">New hires: {hiringSim.count}</label>
            <input className="mt-2 w-full accent-[#8d4f27]" type="range" min={1} max={50} value={hiringSim.count} onChange={(e) => setHiringSim({ ...hiringSim, count: Number(e.target.value) })} />
            <label className="mt-4 block text-xs uppercase tracking-[0.12em] text-[#7b6d5b]">Avg salary ($k): {hiringSim.salary}</label>
            <input className="mt-2 w-full accent-[#8d4f27]" type="range" min={50} max={300} value={hiringSim.salary} onChange={(e) => setHiringSim({ ...hiringSim, salary: Number(e.target.value) })} />
            <p className="mt-5 text-sm text-[#5e5243]">Runway pressure from hiring: <span className="font-semibold text-[#9a461f]">-{runwayDropMonths.toFixed(1)} months</span></p>
            <p className="mt-1 text-xs text-[#7c6c58]">Includes cash policy multiplier for realistic finance planning.</p>
          </article>

          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-6">
            <div className="mb-4 flex items-center justify-between">
              <div className="inline-flex items-center gap-2 text-[#71562f] font-semibold"><Globe className="h-4 w-4" />Revenue Stress Test</div>
              <button 
                onClick={() => saveScenario("revenue", { shift: revenueShift, planningMode, cashPolicy }, { runway_extension: revenueRunwayEffect })}
                className="text-xs text-[#8d4f27] font-bold hover:underline"
              >
                Save Snapshot
              </button>
            </div>
            <label className="text-xs uppercase tracking-[0.12em] text-[#7b6d5b]">Revenue shift: {revenueShift}%</label>
            <input className="mt-2 w-full accent-emerald-600" type="range" min={-30} max={40} value={revenueShift} onChange={(e) => setRevenueShift(Number(e.target.value))} />
            <p className="mt-5 text-sm text-[#5e5243]">Potential runway contribution: <span className={`font-semibold ${revenueRunwayEffect >= 0 ? "text-[#276749]" : "text-[#9a461f]"}`}>{revenueRunwayEffect >= 0 ? "+" : ""}{revenueRunwayEffect.toFixed(1)} months</span></p>
            <p className="mt-1 text-xs text-[#7c6c58]">Use negative values to model churn or pricing pressure.</p>
          </article>
        </section>

        <section className="rounded-2xl border border-[#d7c8b5] bg-[#fff9ee] p-5">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 text-sm font-semibold text-[#5f4c33]"><Wallet className="h-4 w-4" />Finance Decision Signal</p>
              <p className="mt-1 text-sm text-[#5e5243]">{recommendationText}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-bold uppercase ${
                operatingSignal === "healthy"
                  ? "bg-[#e8f6ea] text-[#1f7a41]"
                  : operatingSignal === "caution"
                    ? "bg-[#fff1dc] text-[#9a5a13]"
                    : "bg-[#ffe7e2] text-[#a33d2e]"
              }`}>
                {operatingSignal === "healthy" ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
                {operatingSignal}
              </span>
              <button
                onClick={() => openChat(`Given planning mode ${planningMode} and cash policy ${cashPolicy}, propose a 90-day finance operating plan. Inputs: hires=${hiringSim.count}, avg_salary_k=${hiringSim.salary}, revenue_shift=${revenueShift}%.`) }
                className="rounded-lg bg-[#2a2118] px-3 py-2 text-xs font-semibold text-[#fff4e4] hover:bg-[#1f1812]"
              >
                Ask finance agent for plan
              </button>
            </div>
          </div>
        </section>

        {history.length > 0 && (
          <section className="space-y-4">
            <h2 className="text-xl font-bold text-[#2c2013]">Saved Scenarios</h2>
            <div className="grid gap-3">
              {history.map((s) => (
                <div key={s.id} className="flex items-center justify-between p-4 rounded-xl border border-[#ded2c4] bg-white shadow-sm">
                  <div>
                    <p className="font-semibold text-[#2a2017]">{s.name}</p>
                    <p className="text-xs text-[#7b6d5b] uppercase">{s.scenario_type} simulation • {new Date(s.created_at).toLocaleDateString()}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-[#9a461f]">
                      {typeof s.result_data?.runway_drop_months === "number"
                        ? `-${s.result_data.runway_drop_months.toFixed(1)}mo`
                        : typeof s.result_data?.runway_extension === "number"
                          ? `${s.result_data.runway_extension >= 0 ? "+" : ""}${s.result_data.runway_extension.toFixed(1)}mo`
                          : "n/a"}
                    </p>
                    <p className="text-[10px] text-[#7b6d5b]">Runway Effect</p>
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
