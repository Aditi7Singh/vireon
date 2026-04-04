"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import api from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import { Award, BarChart3, BadgeDollarSign, RefreshCw, Sparkles } from "lucide-react";

export default function InvestorPage() {
  const { openChat } = useAppStore();
  const [scorecard, setScorecard] = useState<any>(null);
  const [benchmark, setBenchmark] = useState<any>(null);
  const [fundraising, setFundraising] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [scorecardData, benchmarkData] = await Promise.all([
          api.getScorecard(),
          api.getBenchmarks(),
        ]);
        setScorecard(scorecardData);
        setBenchmark(benchmarkData);
        setFundraising({
          score: Math.min(100, Math.max(0, (scorecardData.runway_months || 0) * 5 + (scorecardData.arr > 0 ? 20 : 0))),
          status: (scorecardData.runway_months || 0) >= 12 ? "ready" : "watch",
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load investor data.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Investor Readiness" />
      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Award className="h-3.5 w-3.5" />
                Board and investor package
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Investor-ready view</h1>
              <p className="mt-2 text-sm text-[#5f5344]">A concise snapshot of runway, efficiency, and benchmark position.</p>
            </div>
            <button
              onClick={() => openChat("Generate an investor-ready financial summary with risks, strengths, and next steps.")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
            >
              <Sparkles className="h-4 w-4" />
              Ask Finley
            </button>
          </div>
        </section>

        {error && <div className="rounded-2xl border border-[#ebc1b8] bg-[#fff1ee] px-4 py-3 text-sm text-[#9f3f30]">{error}</div>}

        <section className="grid gap-4 md:grid-cols-4">
          {[
            { label: "Cash", value: formatCurrency(scorecard?.total_cash || 0) },
            { label: "Runway", value: `${Number(scorecard?.runway_months || 0).toFixed(1)} months` },
            { label: "ARR", value: formatCurrency(scorecard?.arr || 0) },
            { label: "Fundraising score", value: `${fundraising?.score || 0}/100` },
          ].map((item) => (
            <article key={item.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{item.label}</p>
              <p className="mt-2 text-2xl font-semibold text-[#2a2017]">{item.value}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-[#87602a]" />
              <h2 className="text-lg font-semibold text-[#2a2017]">Benchmark summary</h2>
            </div>
            <div className="mt-4 space-y-3 text-sm text-[#5f5344]">
              {(benchmark?.metrics || []).map((metric: any) => (
                <div key={metric.name} className="rounded-xl border border-[#e8dcc9] bg-[#fff8ec] px-4 py-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-[#2a2017]">{metric.name}</span>
                    <span className="font-semibold text-[#9a461f]">{metric.value}</span>
                  </div>
                  <p className="mt-1 text-xs text-[#7b6d5b]">Target: {metric.benchmark}</p>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
            <div className="flex items-center gap-2">
              <BadgeDollarSign className="h-4 w-4 text-[#87602a]" />
              <h2 className="text-lg font-semibold text-[#2a2017]">Investor checklist</h2>
            </div>
            <div className="mt-4 space-y-3 text-sm text-[#5f5344]">
              <p>Runway: {Number(scorecard?.runway_months || 0).toFixed(1)} months</p>
              <p>Burn: {formatCurrency(scorecard?.monthly_net_burn || 0)} monthly net burn</p>
              <p>Benchmark narrative: {(benchmark?.summary || "Internal benchmark score available.")}</p>
              <p>Readiness: {fundraising?.status || "watch"}</p>
            </div>
          </article>
        </section>

        {loading && (
          <div className="flex items-center gap-2 rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-4 text-sm text-[#6f5f4b]">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading investor data...
          </div>
        )}
      </div>
    </div>
  );
}
