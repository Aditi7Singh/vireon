"use client";

import Link from "next/link";
import { ArrowRight, Bot, Zap, Shield, TrendingUp, Globe, Cpu, Hexagon } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#020617] text-slate-200 font-sans selection:bg-indigo-500/30 overflow-hidden relative">
      {/* Cinematic Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-500/5 blur-[120px] rounded-full animate-pulse-slow" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-emerald-500/5 blur-[120px] rounded-full animate-pulse-slow" />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-100 contrast-150" />
      </div>

      <header className="relative z-50 flex items-center justify-between px-8 py-8 lg:px-12 max-w-[1800px] mx-auto">
        <div className="flex items-center gap-3 group cursor-pointer">
          <div className="relative">
            <div className="w-10 h-10 bg-gradient-to-tr from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-500">
              <Hexagon className="w-6 h-6 text-white" />
            </div>
            <div className="absolute inset-0 bg-indigo-500 blur-xl opacity-0 group-hover:opacity-40 transition-opacity" />
          </div>
          <span className="text-2xl font-black tracking-tighter text-white font-outfit uppercase">SeedlingLabs</span>
        </div>

        <nav className="hidden md:flex items-center gap-10">
          {["Intelligence", "Security", "Infrastructure", "Vision"].map((item) => (
            <Link key={item} href="#" className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 hover:text-white transition-colors">{item}</Link>
          ))}
        </nav>

        <Link
          href="/dashboard"
          className="px-6 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-[10px] font-black uppercase tracking-widest text-white transition-all hover:border-white/20 backdrop-blur-md"
        >
          Access Portal
        </Link>
      </header>

      <main className="relative z-10 flex flex-col items-center justify-center px-6 pt-20 lg:pt-32 pb-40">
        <div className="text-center space-y-8 max-w-5xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-black uppercase tracking-widest animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <Cpu className="w-3.5 h-3.5" />
            Strategic Growth Intelligence
          </div>

          <h1 className="text-6xl md:text-8xl lg:text-9xl font-black text-white font-outfit tracking-tight leading-[0.9] animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-100">
            Building the <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500">Financial Future.</span>
          </h1>

          <p className="mt-8 text-lg md:text-xl text-slate-400 max-w-3xl mx-auto font-medium leading-relaxed animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-200">
            SeedlingLabs pioneers the next generation of business intelligence.
            Through our flagship platform, <span className="text-white font-bold">Vireon</span>, we bridge the gap between complex ERP data and strategic executive decisions.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 mt-12 animate-in fade-in slide-in-from-bottom-16 duration-1000 delay-300">
            <Link
              href="/dashboard"
              className="group relative px-10 py-5 bg-indigo-600 rounded-2xl overflow-hidden hover:scale-105 active:scale-95 transition-all shadow-2xl shadow-indigo-600/40"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-indigo-400 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative flex items-center gap-3">
                <span className="text-[12px] font-black uppercase tracking-[0.2em] text-white">Enter Vireon Portal</span>
                <ArrowRight className="w-4 h-4 text-white group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            <Link href="#intel" className="px-10 py-5 rounded-2xl border border-white/10 hover:border-white/20 transition-all text-[12px] font-black uppercase tracking-[0.2em] text-slate-400 hover:text-white backdrop-blur-md">
              Our Vision
            </Link>
          </div>
        </div>

        {/* Feature Grid - Cinematic Cards */}
        <div id="intel" className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-40 max-w-[1400px] w-full animate-in fade-in slide-in-from-bottom-20 duration-1000 delay-500">
          {[
            {
              title: "Autonomous Analytics",
              desc: "Vireon's core engine detects financial leakage and anomalies with machine-grade precision.",
              icon: Bot,
              color: "text-indigo-400",
              bg: "bg-indigo-500/5",
            },
            {
              title: "Unified Resilience",
              desc: "Strategic runway modeling derived from real-time ERP data integration.",
              icon: Shield,
              color: "text-emerald-400",
              bg: "bg-emerald-500/5",
            },
            {
              title: "Capital Velocity",
              desc: "Accelerating the flow of capital intelligence for high-performance scale-ups.",
              icon: TrendingUp,
              color: "text-purple-400",
              bg: "bg-purple-500/5",
            },
          ].map((feature, i) => (
            <div key={i} className="group glass-card p-10 rounded-[40px] hover:bg-white/[0.05] transition-all duration-700 hover:-translate-y-2">
              <div className={`w-14 h-14 ${feature.bg} rounded-[20px] flex items-center justify-center mb-8 border border-white/5 transition-transform group-hover:scale-110 duration-500`}>
                <feature.icon className={`h-7 w-7 ${feature.color}`} />
              </div>
              <h3 className="text-2xl font-black text-white font-outfit mb-4">{feature.title}</h3>
              <p className="text-slate-500 font-medium leading-relaxed group-hover:text-slate-300 transition-colors">
                {feature.desc}
              </p>
            </div>
          ))}
        </div>
      </main>

      <footer className="relative z-10 border-t border-white/5 bg-black/40 backdrop-blur-3xl py-12">
        <div className="max-w-[1400px] mx-auto px-8 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="flex items-center gap-2 opacity-50 grayscale hover:grayscale-0 transition-all cursor-pointer">
            <Hexagon className="w-5 h-5 text-indigo-500" />
            <span className="text-xs font-black uppercase tracking-widest text-slate-400">© 2026 SeedlingLabs Intelligence</span>
          </div>
          <div className="flex items-center gap-8">
            {["Privacy", "Security", "Scale", "ERP Connect"].map(l => (
              <Link key={l} href="#" className="text-[10px] font-black uppercase tracking-widest text-slate-600 hover:text-indigo-400 transition-all">{l}</Link>
            ))}
          </div>
          <div className="flex items-center gap-4">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Vireon Status: Online</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
