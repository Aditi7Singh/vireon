"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import api from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { ArrowUpRight, Sparkles, Target, TrendingUp } from "lucide-react";

export default function BenchmarkingPage() {
  const [benchmarks, setBenchmarks] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { openChat } = useAppStore();

  useEffect(() => {
    const loadData = async () => {
      try {
        setError(null);
        const data = await api.getBenchmarks();
        setBenchmarks(data || {
          metrics: [
            {
              name: "Rule of 40",
              value: "0.0%",
              status: "Pending Data",
              benchmark: "40.0%",
              description: "Growth Rate + Profit Margin"
            },
            {
              name: "Burn Multiple",
              value: "0.00x",
              status: "Pending Data",
              benchmark: "< 1.5x",
              description: "Efficiency of burning capital for growth"
            },
            {
              name: "Net Revenue Retention",
              value: "0%",
              status: "Pending Data",
              benchmark: "> 110%",
              description: "LTM revenue from existing customers"
            }
          ],
          summary: "Benchmark card is ready. Add monthly metrics to see live SaaS health scoring."
        });
      } catch (err) {
        setError("Failed to load benchmarks");
        setBenchmarks({
          metrics: [
            {
              name: "Rule of 40",
              value: "—",
              status: "Error",
              benchmark: "40.0%",
              description: "Growth Rate + Profit Margin"
            },
            {
              name: "Burn Multiple",
              value: "—",
              status: "Error",
              benchmark: "< 1.5x",
              description: "Efficiency of burning capital for growth"
            },
            {
              name: "Net Revenue Retention",
              value: "—",
              status: "Error",
              benchmark: "> 110%",
              description: "LTM revenue from existing customers"
            }
          ],
          summary: "Unable to load benchmarks at this time."
        });
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
        <TopBar title="Performance Intelligence" />
        <div className="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
          <div className="flex h-96 items-center justify-center">
            <div className="text-center">
              <div className="animate-pulse text-sm text-[#8a7b68]">Loading benchmarks...</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Performance Intelligence" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Target className="h-3.5 w-3.5" />
                Live benchmark feed
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Operational Benchmarking</h1>
              <p className="mt-2 text-sm text-[#5f5344]">{benchmarks?.summary || "Compare financial efficiency against cohort baselines."}</p>
            </div>
            <button
              onClick={() => openChat("Strategic Advisory for Rule of 40 performance")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
            >
              <Sparkles className="h-4 w-4" />
              Consult AI advisor
            </button>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          {(benchmarks?.metrics || []).map((m: any, i: number) => {
            const getStatusColor = (status: string) => {
              switch(status?.toLowerCase()) {
                case 'excellent': return { bg: 'bg-emerald-50', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-700' };
                case 'great': return { bg: 'bg-blue-50', border: 'border-blue-200', badge: 'bg-blue-100 text-blue-700' };
                case 'good': return { bg: 'bg-amber-50', border: 'border-amber-200', badge: 'bg-amber-100 text-amber-700' };
                case 'monitor': return { bg: 'bg-orange-50', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-700' };
                case 'critical': return { bg: 'bg-red-50', border: 'border-red-200', badge: 'bg-red-100 text-red-700' };
                default: return { bg: 'bg-gray-50', border: 'border-gray-200', badge: 'bg-gray-100 text-gray-700' };
              }
            };
            const colors = getStatusColor(m.status);
            return (
              <article key={i} className={`rounded-2xl transition-all border-2 ${colors.border} ${colors.bg} p-6 flex flex-col hover:shadow-[0_8px_24px_rgba(0,0,0,0.08)] hover:-translate-y-1`}>
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] font-semibold text-[#776b5a] mb-1">{m.name}</p>
                    <p className="text-4xl font-bold text-[#2a2017]">{m.value}</p>
                  </div>
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full whitespace-nowrap ${colors.badge}`}>
                    {m.status}
                  </span>
                </div>
                
                <div className="space-y-2 mb-4 pb-4 border-b border-black/5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[#696156] font-medium">Target:</span>
                    <span className="text-sm font-semibold text-[#2a2017]">{m.benchmark}</span>
                  </div>
                  <p className="text-xs leading-relaxed text-[#5f5344]">{m.description}</p>
                </div>

                {m.narrative && (
                  <p className="text-xs text-[#6b5d4f] bg-white/60 p-3 rounded-lg mb-4 flex-grow italic">{m.narrative}</p>
                )}
                
                <button 
                  onClick={() => openChat(`Help me improve ${m.name}: ${m.narrative || m.description}`)}
                  className="inline-flex items-center gap-2 text-xs font-bold text-[#8a5a1e] hover:text-[#6b4712] transition-colors hover:bg-black/5 px-2.5 py-1.5 rounded-lg -ml-2.5"
                >
                  Get advice 
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </button>
              </article>
            );
          })}
        </section>
      </div>
    </div>
  );
}
