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
import { useAppStore } from "@/lib/store";

export default function BenchmarkingPage() {
    const [benchmarks, setBenchmarks] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const { openChat } = useAppStore();

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
            <div className="flex items-center justify-center min-h-screen bg-[#020617]">
                <div className="w-16 h-16 border-4 border-indigo-500/10 border-t-indigo-500 rounded-full animate-spin shadow-[0_0_30px_rgba(99,102,241,0.2)]" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 pb-20">
            <TopBar title="Performance Intelligence" />

            <div className="p-8 max-w-[1600px] mx-auto space-y-10">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
                    <div className="space-y-4">
                        <div className="flex items-center gap-3">
                            <span className="px-3 py-1 bg-slate-900 text-slate-400 text-[10px] font-bold uppercase tracking-wider rounded border border-slate-800">
                                Benchmarks
                            </span>
                            <span className="px-3 py-1 bg-emerald-500/10 text-emerald-500 text-[10px] font-bold uppercase tracking-wider rounded border border-emerald-500/10 flex items-center gap-2">
                                Live Data
                            </span>
                        </div>
                        <h1 className="text-4xl font-bold text-white tracking-tight"> Efficiency <span className="text-slate-400">Metrics</span> </h1>
                        <p className="text-slate-500 font-medium text-xs max-w-xl">
                            Competitive operational scoring versus top-quartile SaaS cohorts.
                        </p>
                    </div>

                    <div className="flex items-center gap-4">
                        <button className="btn-secondary">
                            <BarChart className="w-4 h-4 text-indigo-500" />
                            Detailed Report
                        </button>
                    </div>
                </div>

                {/* Score Summary Box */}
                <div className="glass-card rounded-2xl p-8 border-slate-800 relative overflow-hidden group">
                    <div className="relative z-10 flex flex-col md:flex-row items-center gap-10">
                        <div className="w-24 h-24 rounded-2xl bg-indigo-600 flex items-center justify-center shadow-lg shrink-0">
                            <ShieldCheck className="w-12 h-12 text-white" />
                        </div>
                        <div className="space-y-4 flex-1 text-center md:text-left">
                            <h2 className="text-2xl font-bold text-white tracking-tight">Operational Health Index</h2>
                            <p className="text-base font-medium text-slate-400 leading-relaxed uppercase tracking-wider">
                                {benchmarks?.summary || "Analyzing efficiency metrics..."}
                            </p>
                            <div className="flex flex-wrap justify-center md:justify-start gap-3">
                                <div className="flex items-center gap-2 px-4 py-1.5 bg-slate-800 rounded-lg border border-slate-700">
                                    <Target className="w-3.5 h-3.5 text-indigo-500" />
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-300">Cohort: Series A</span>
                                </div>
                                <div className="flex items-center gap-2 px-4 py-1.5 bg-emerald-500/10 rounded-lg border border-emerald-500/10">
                                    <Zap className="w-3.5 h-3.5 text-emerald-500" />
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-500">Momentum: 1.4x Elite</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Benchmark Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
                    {benchmarks?.metrics?.map((m: any, i: number) => (
                        <div key={i} className="glass-card rounded-[48px] p-10 group hover:bg-white/[0.03] border-white/5 hover:border-white/10 transition-all duration-700 hover:shadow-2xl">
                            <div className="flex items-center justify-between mb-10">
                                <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/5 flex items-center justify-center group-hover:bg-indigo-600 group-hover:border-indigo-500 transition-all duration-500 shadow-2xl">
                                    <TrendingUp className="w-6 h-6 text-slate-500 group-hover:text-white transition-colors duration-500" />
                                </div>
                                <span className={cn(
                                    "px-4 py-1.5 rounded-full text-[9px] font-black uppercase tracking-[0.2em] border",
                                    m.status === "Healthy" || m.status === "Great" ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" :
                                        m.status === "Monitor" ? "bg-amber-500/10 border-amber-500/20 text-amber-500" : "bg-rose-500/10 border-rose-500/20 text-rose-500"
                                )}>
                                    {m.status}
                                </span>
                            </div>

                            <h3 className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-600 mb-3 font-outfit">{m.name}</h3>
                            <div className="flex items-baseline gap-4 mb-6">
                                <span className="text-5xl font-black text-white font-outfit tracking-tighter uppercase">{m.value}</span>
                                <span className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Base: {m.benchmark}</span>
                            </div>
                            <p className="text-xs font-bold text-slate-500 leading-relaxed min-h-[40px] uppercase tracking-wide opacity-80">
                                {m.description}
                            </p>

                            <div className="mt-10 pt-10 border-t border-white/5 group-hover:border-white/10 transition-colors">
                                <button className="w-full flex items-center justify-center gap-3 group/btn py-1 text-[10px] font-black uppercase tracking-[0.2em] text-indigo-400 hover:text-indigo-300 transition-all">
                                    Analyze Node
                                    <ArrowUpRight className="w-4 h-4 group-hover/btn:translate-x-1 group-hover/btn:-translate-y-1 transition-transform" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Secondary Content */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
                    <div className="lg:col-span-12 glass-card rounded-[48px] p-12 border-white/5">
                        <div className="flex items-center justify-between mb-12">
                            <h3 className="text-2xl font-black text-white font-outfit uppercase tracking-tighter">Global Market Intelligence</h3>
                            <div className="px-4 py-1.5 bg-indigo-600 text-white text-[9px] font-black uppercase tracking-[0.2em] rounded-full shadow-2xl">
                                Live Stream
                            </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
                            {[
                                { title: "SaaS Multiples stage recovery vs Treasury Yields", date: "02:00 UTC", source: "Seedling News", icon: BarChart },
                                { title: "Tier 1 VC expectations for Rule of 40 in 2026", date: "05:00 UTC", source: "Market Pulse", icon: Target },
                                { title: "Infrastructure Optimization: Emerging Standard", date: "1 DAY AGO", source: "Research", icon: Sparkles }
                            ].map((item, idx) => (
                                <div key={idx} className="flex flex-col gap-4 group cursor-pointer p-6 hover:bg-white/5 rounded-3xl transition-all border border-transparent hover:border-white/5">
                                    <div className="flex items-center justify-between">
                                        <span className="text-[9px] font-black text-indigo-500 uppercase tracking-[0.2em]">{item.source}</span>
                                        <span className="text-[9px] text-slate-500 font-black uppercase tracking-widest">{item.date}</span>
                                    </div>
                                    <p className="text-sm font-black text-white uppercase tracking-wider leading-relaxed group-hover:text-indigo-400 transition-colors">{item.title}</p>
                                    <div className="mt-auto pt-4 flex items-center gap-2 text-[9px] font-black text-slate-600 uppercase tracking-[0.2em] group-hover:text-slate-400 transition-colors">
                                        Access Node <ArrowUpRight className="w-3 h-3" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="lg:col-span-12 bg-indigo-600 rounded-[56px] p-12 text-white relative overflow-hidden group shadow-2xl">
                        <Zap className="absolute -right-20 -bottom-20 w-80 h-80 opacity-10 rotate-12 group-hover:rotate-45 transition-transform duration-1000" />
                        <div className="relative z-10 flex flex-col lg:flex-row items-center justify-between gap-12">
                            <div className="max-w-3xl space-y-6 text-center lg:text-left">
                                <h3 className="text-3xl font-black font-outfit uppercase tracking-tighter">Strategic Advisory Vector</h3>
                                <p className="text-lg font-bold opacity-80 leading-relaxed uppercase tracking-wide">
                                    "Your current Rule of 40 score of <span className="text-white font-black underline decoration-white/30">42.1%</span> indicates an outperformance of 85% of your direct peer group. Strategic pivot to <span className="italic">expansion modeling</span> is recommended."
                                </p>
                            </div>
                            <button
                                onClick={() => openChat("Strategic Advisory for Rule of 40 performance")}
                                className="flex items-center gap-4 px-10 py-6 bg-white text-indigo-700 rounded-2xl text-[10px] font-black uppercase tracking-[0.25em] shadow-3xl hover:bg-slate-50 active:scale-95 transition-all shrink-0"
                            >
                                <Sparkles className="w-5 h-5 text-indigo-600 animate-pulse" />
                                Consult Agent Node
                            </button>
                        </div>
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
