"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import api from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { ArrowUpRight, Sparkles, Target, TrendingUp } from "lucide-react";

export default function BenchmarkingPage() {
  const [benchmarks, setBenchmarks] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { openChat } = useAppStore();

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await api.getBenchmarks();
        setBenchmarks(data);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, []);

  if (isLoading) {
    return <div className="min-h-screen bg-[#f6f3ee]" />;
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
          {(benchmarks?.metrics || []).map((m: any, i: number) => (
            <article key={i} className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5">
              <div className="flex items-center justify-between">
                <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{m.name}</p>
                <TrendingUp className="h-4 w-4 text-[#87602a]" />
              </div>
              <p className="mt-2 text-2xl font-semibold text-[#2a2017]">{m.value}</p>
              <p className="mt-1 text-xs text-[#6f6252]">Benchmark: {m.benchmark}</p>
              <p className="mt-2 text-xs text-[#7e715f]">{m.description}</p>
              <button className="mt-4 inline-flex items-center gap-1 text-xs font-medium text-[#8a5a1e]">Analyze <ArrowUpRight className="h-3.5 w-3.5" /></button>
            </article>
          ))}
        </section>
      </div>
    </div>
  );
}
