"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import { 
    TrendingUp, 
    ArrowUpRight, 
    ArrowDownRight, 
    Info, 
    Target, 
    ShieldCheck, 
    Zap,
    Sparkles,
    BarChart
} from "lucide-react";
import api from "@/lib/api";
import { cn } from "@/lib/utils";

export default function BenchmarkingPage() {
    const [benchmarks, setBenchmarks] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            try {
                const data = await api.getBenchmarks();
                setBenchmarks(data);
            } catch (err) {
                console.error("Error loading benchmarks:", err);
            } finally {
                setIsLoading(false);
            }
        };
        loadData();
    }, []);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-slate-950">
                <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950/50 pb-20">
            <TopBar title="SaaS Performance Intelligence" />

            <div className="p-8 max-w-[1400px] mx-auto space-y-12">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                    <div>
                        <div className="flex items-center gap-2 mb-3">
                            <span className="px-3 py-1 bg-indigo-500/10 text-indigo-500 text-[10px] font-black uppercase tracking-widest rounded-full border border-indigo-500/20">
                                Global Industry Benchmarks
                            </span>
                            <span className="px-3 py-1 bg-emerald-500/10 text-emerald-500 text-[10px] font-black uppercase tracking-widest rounded-full border border-emerald-500/20 flex items-center gap-1.5">
                                <div className="w-1 h-1 bg-emerald-500 rounded-full animate-pulse" />
                                Live Engine
                            </span>
                        </div>
                        <h1 className="text-4xl font-black text-slate-900 dark:text-white font-outfit tracking-tight"> Efficiency Scoring </h1>
                        <p className="text-slate-500 mt-2 font-medium max-w-xl italic">
                            Quantifying your operational performance against top-quartile SaaS companies at your current stage and ARR bracket.
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <button className="flex items-center gap-2 px-6 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl text-xs font-black uppercase tracking-widest text-slate-600 dark:text-slate-300 hover:border-indigo-500/30 transition-all shadow-sm">
                            <BarChart className="w-4 h-4" />
                            Comparative Chart
                        </button>
                    </div>
                </div>

                {/* Score Summary Box */}
                <div className="glass-card rounded-[40px] p-12 border border-slate-200 dark:border-slate-800/50 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-8">
                       <Sparkles className="w-8 h-8 text-indigo-500/20 group-hover:scale-125 transition-transform duration-700" />
                    </div>
                    <div className="relative z-10 flex flex-col md:flex-row items-center gap-10">
                        <div className="w-32 h-32 rounded-[32px] bg-indigo-600 flex items-center justify-center shadow-2xl shadow-indigo-600/40 shrink-0">
                            <ShieldCheck className="w-12 h-12 text-white" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-black text-slate-900 dark:text-white font-outfit tracking-tight mb-2">Operational Health Summary</h2>
                            <p className="text-lg font-medium text-slate-600 dark:text-slate-300 leading-relaxed mb-4">
                                {benchmarks?.summary || "Analyzing efficiency vectors..."}
                            </p>
                            <div className="flex flex-wrap gap-4">
                                <div className="flex items-center gap-2 px-4 py-2 bg-indigo-500/10 rounded-xl">
                                    <Target className="w-4 h-4 text-indigo-500" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-indigo-600">Cohort: Series A / Infra</span>
                                </div>
                                <div className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 rounded-xl">
                                    <Zap className="w-4 h-4 text-emerald-500" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-emerald-600">Growth Index: 1.4x Elite</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Benchmark Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {benchmarks?.metrics?.map((m: any, i: number) => (
                        <div key={i} className="glass-card rounded-[40px] p-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 group hover:border-indigo-500/20 transition-all duration-500 hover:shadow-2xl hover:shadow-indigo-500/10">
                            <div className="flex items-center justify-between mb-8">
                                <div className="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center group-hover:bg-indigo-600 transition-colors duration-500">
                                    <TrendingUp className="w-5 h-5 text-slate-600 dark:text-slate-400 group-hover:text-white transition-colors" />
                                </div>
                                <span className={cn(
                                    "px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest",
                                    m.status === "Healthy" || m.status === "Great" ? "bg-emerald-500/10 text-emerald-600" :
                                    m.status === "Monitor" ? "bg-amber-500/10 text-amber-600" : "bg-rose-500/10 text-rose-600"
                                )}>
                                    {m.status}
                                </span>
                            </div>

                            <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-2">{m.name}</h3>
                            <div className="flex items-baseline gap-3 mb-4">
                                <span className="text-4xl font-black text-slate-900 dark:text-white font-outfit tracking-tighter">{m.value}</span>
                                <span className="text-xs font-bold text-slate-400">vs {m.benchmark} benchmark</span>
                            </div>
                            <p className="text-xs font-medium text-slate-500 leading-relaxed min-h-[40px]">
                                {m.description}
                            </p>
                            
                            <div className="mt-8 pt-8 border-t border-slate-100 dark:border-slate-800/50">
                                <button className="w-full flex items-center justify-center gap-2 group/btn py-1 text-[10px] font-black uppercase tracking-[0.1em] text-indigo-600 hover:text-indigo-500">
                                    View breakdown
                                    <ArrowUpRight className="w-3.5 h-3.5 group-hover/btn:translate-x-1 group-hover/btn:-translate-y-1 transition-transform" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Secondary Feature: Industry News/Alerts related to CFO role */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                   <div className="glass-card rounded-[40px] p-10 border border-slate-200 dark:border-slate-800/50">
                      <h3 className="text-lg font-black text-slate-900 dark:text-white font-outfit tracking-tight mb-8">Industry Intelligence</h3>
                      <div className="space-y-6">
                         {[
                            { title: "SVB Market Update: Treasury Yield Impact", date: "2 hours ago", source: "Bloomberg" },
                            { title: "SaaS Multiples: B2B Software stages recovery", date: "5 hours ago", source: "SaasStr" },
                            { title: "AI Computation Costs Trends: 2026 Forecast", date: "1 day ago", source: "Seedling Research" }
                         ].map((item, idx) => (
                            <div key={idx} className="flex flex-col gap-1 group cursor-pointer">
                               <div className="flex items-center justify-between">
                                  <span className="text-[9px] font-black text-indigo-500 uppercase tracking-widest">{item.source}</span>
                                  <span className="text-[9px] text-slate-400 font-bold">{item.date}</span>
                               </div>
                               <p className="font-bold text-slate-900 dark:text-white group-hover:text-indigo-500 transition-colors">{item.title}</p>
                            </div>
                         ))}
                      </div>
                   </div>

                   <div className="glass-card rounded-[40px] p-10 border border-slate-200 dark:border-slate-800/50 bg-slate-900 text-white">
                      <h3 className="text-lg font-black font-outfit tracking-tight mb-4">Neural Advisory</h3>
                      <p className="text-sm text-slate-400 font-medium leading-relaxed mb-10 italic">
                         "Based on your current Rule of 40 score of 42.1%, you are outperforming 85% of your direct peer group. We recommend shifting focus from survival to aggressive expansion Tier 2 modeling."
                      </p>
                      <button className="flex items-center gap-2 px-8 py-4 bg-white text-slate-950 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:scale-105 transition-all">
                         <Sparkles className="w-4 h-4 text-indigo-600" />
                         Consult Strategic Agent
                      </button>
                   </div>
                </div>
            </div>
        </div>
    );
}

function Field({ label, type = "text", placeholder, defaultValue, options }: any) {
    return (
        <div className="space-y-2">
            <label className="block text-[10px] font-black uppercase tracking-widest text-slate-400">
                {label}
            </label>
            {type === "select" ? (
                <select className="w-full h-14 px-6 border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 text-sm font-bold text-slate-900 dark:text-white ring-indigo-500/10 focus:ring-4 focus:border-indigo-500 focus:outline-none appearance-none cursor-pointer">
                    {options.map((opt: string) => <option key={opt}>{opt}</option>)}
                </select>
            ) : (
                <input
                    type={type}
                    placeholder={placeholder}
                    defaultValue={defaultValue}
                    className="w-full h-14 px-6 border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 text-sm font-bold text-slate-900 dark:text-white ring-indigo-500/10 focus:ring-4 focus:border-indigo-500 focus:outline-none"
                />
            )}
        </div>
    );
}
