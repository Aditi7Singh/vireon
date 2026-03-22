"use client";

import { useState, useEffect } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { Sparkles, Briefcase, Globe, Target } from "lucide-react";

export default function ScenariosPage() {
  const { openChat } = useAppStore();
  const [hiringSim, setHiringSim] = useState({ count: 8, salary: 100 });
  const [revenueShift, setRevenueShift] = useState(12);
  const [history, setHistory] = useState<any[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  const runwayImpact = (hiringSim.count * hiringSim.salary) / 800;
  const extension = Math.max(0.4, revenueShift / 3.2);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/planning/scenarios/history?company_id=demo`);
      if (res.ok) setHistory(await res.json());
    } catch (e) { console.error(e); }
  };

  useEffect(() => { fetchHistory(); }, []);

  const saveScenario = async (type: string, data: any, result: any) => {
    setIsSaving(true);
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/planning/scenarios/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_id: "demo",
          name: `${type} Plan - ${new Date().toLocaleDateString()}`,
          scenario_type: type,
          input_data: data,
          result_data: result
        })
      });
      fetchHistory();
    } catch (e) { console.error(e); }
    finally { setIsSaving(false); }
  };

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
              <p className="mt-2 text-sm text-[#5f5344]">Run hiring and revenue stress tests to quantify runway impact instantly.</p>
            </div>
            <button
              onClick={() => openChat("Advanced Predictive Modeling Request")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
            >
              <Sparkles className="h-4 w-4" />
              New simulation
            </button>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-6">
            <div className="mb-4 flex items-center justify-between">
              <div className="inline-flex items-center gap-2 text-[#71562f] font-semibold"><Briefcase className="h-4 w-4" />Hiring Simulation</div>
              <button 
                onClick={() => saveScenario("hiring", hiringSim, { impact: runwayImpact })}
                disabled={isSaving}
                className="text-xs text-indigo-600 font-bold hover:underline"
              >
                {isSaving ? "Saving..." : "Save Snapshot"}
              </button>
            </div>
            <label className="text-xs uppercase tracking-[0.12em] text-[#7b6d5b]">New hires: {hiringSim.count}</label>
            <input className="mt-2 w-full accent-indigo-600" type="range" min={1} max={50} value={hiringSim.count} onChange={(e) => setHiringSim({ ...hiringSim, count: Number(e.target.value) })} />
            <label className="mt-4 block text-xs uppercase tracking-[0.12em] text-[#7b6d5b]">Avg salary ($k): {hiringSim.salary}</label>
            <input className="mt-2 w-full accent-indigo-600" type="range" min={50} max={300} value={hiringSim.salary} onChange={(e) => setHiringSim({ ...hiringSim, salary: Number(e.target.value) })} />
            <p className="mt-5 text-sm text-[#5e5243]">Estimated runway impact: <span className="font-semibold text-[#9a461f]">-{runwayImpact.toFixed(1)} months</span></p>
          </article>

          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-6">
            <div className="mb-4 flex items-center justify-between">
              <div className="inline-flex items-center gap-2 text-[#71562f] font-semibold"><Globe className="h-4 w-4" />Revenue Stress Test</div>
              <button 
                onClick={() => saveScenario("revenue", { shift: revenueShift }, { extension })}
                className="text-xs text-indigo-600 font-bold hover:underline"
              >
                Save Snapshot
              </button>
            </div>
            <label className="text-xs uppercase tracking-[0.12em] text-[#7b6d5b]">Revenue shift: {revenueShift}%</label>
            <input className="mt-2 w-full accent-emerald-600" type="range" min={-30} max={40} value={revenueShift} onChange={(e) => setRevenueShift(Number(e.target.value))} />
            <p className="mt-5 text-sm text-[#5e5243]">Potential runway extension: <span className="font-semibold text-[#276749]">+{extension.toFixed(1)} months</span></p>
          </article>
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
                      {s.result_data?.impact ? `-${s.result_data.impact.toFixed(1)}mo` : `+${s.result_data?.extension?.toFixed(1)}mo`}
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
    </div>
  );
}
