"use client";

import TopBar from "@/components/TopBar";
import { useRunway, useScorecard } from "@/hooks/useFinancialData";
import { useAppStore } from "@/lib/store";
import { formatCurrency, formatCompactNumber, cn } from "@/lib/utils";
import {
   TrendingDown,
   TrendingUp,
   AlertTriangle,
   Calendar,
   Zap,
   Sparkles,
   Info,
   Clock,
   Shield,
   ArrowRight,
   Target,
   Waves,
   Hexagon,
} from "lucide-react";
import {
   AreaChart,
   Area,
   XAxis,
   YAxis,
   CartesianGrid,
   Tooltip,
   ResponsiveContainer
} from "recharts";

const projectionData = [
   { month: "Mar", cash: 250000, burn: 45000 },
   { month: "Apr", cash: 205000, burn: 46000 },
   { month: "May", cash: 159000, burn: 44000 },
   { month: "Jun", cash: 115000, burn: 45000 },
   { month: "Jul", cash: 70000, burn: 47000 },
   { month: "Aug", cash: 23000, burn: 45000 },
];

export default function RunwayPage() {
   const { runway, isLoading } = useRunway();
   const { scorecard } = useScorecard();
   const { openChat } = useAppStore();

   const isLowRunway = runway.runway_months < 6;
   const isHealthyRunway = runway.runway_months >= 12;

   const runwayStatus = isLowRunway
      ? { label: "CRITICAL", color: "text-rose-500", bg: "bg-rose-500/10", border: "border-rose-500/20", shadow: "shadow-rose-500/20", icon: AlertTriangle }
      : isHealthyRunway
         ? { label: "OPTIMIZED", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20", shadow: "shadow-emerald-500/20", icon: Shield }
         : { label: "STABLE", color: "text-indigo-400", bg: "bg-indigo-500/10", border: "border-indigo-500/20", shadow: "shadow-indigo-500/20", icon: Clock };

   return (
      <div className="min-h-screen bg-slate-950 pb-20">
         <TopBar title="Runway & Survival" />

         <div className="p-8 space-y-10 max-w-[1600px] mx-auto">
            {/* Header Section */}
            <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8">
               <div className="space-y-2">
                  <h1 className="text-4xl font-bold text-white tracking-tight">
                     Capital <span className="text-slate-400">Runway</span>
                  </h1>
                  <div className="flex items-center gap-4 text-slate-500 font-medium text-xs">
                     <div className="flex items-center gap-2">
                        <Target className="w-4 h-4" />
                        <span>Focus: Cash Preservation</span>
                     </div>
                     <div className="w-1 h-1 rounded-full bg-slate-700" />
                     <div className={cn("flex items-center gap-2", runwayStatus.color)}>
                        <runwayStatus.icon className="w-4 h-4" />
                        <span>Status: {runwayStatus.label}</span>
                     </div>
                  </div>
               </div>

               <button
                  onClick={() => openChat("Runway Strategic Analysis")}
                  className="btn-secondary"
               >
                  <Zap className="w-4 h-4 text-indigo-500" />
                  Forecast Analysis
               </button>
            </div>

            {/* Life Clock Hero */}
            <div className="glass-card rounded-2xl p-8 border-slate-800 relative overflow-hidden group">
               <div className="flex flex-col xl:flex-row items-center gap-12 relative z-10">
                  <div className="flex-shrink-0 relative">
                     <div className={cn("w-48 h-48 rounded-full flex flex-col items-center justify-center border-8 transition-all bg-slate-900",
                        runwayStatus.border)}>
                        <span className={cn("text-6xl font-bold tracking-tighter leading-none mb-1", runwayStatus.color)}>
                           {runway.runway_months}
                        </span>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Months</span>
                     </div>
                     <div className={cn("absolute -bottom-2 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-xl border flex items-center gap-2 shadow-lg", runwayStatus.bg, runwayStatus.border)}>
                        <runwayStatus.icon className={cn("w-3.5 h-3.5", runwayStatus.color)} />
                        <span className={cn("text-[9px] font-bold uppercase tracking-wider", runwayStatus.color)}>{runwayStatus.label} PROFILE</span>
                     </div>
                  </div>

                  <div className="flex-grow space-y-8 min-w-0">
                     <div>
                        <h2 className="text-2xl font-bold text-white tracking-tight">Depletion Analysis</h2>
                        <p className="text-slate-500 font-medium text-base mt-2 leading-relaxed max-w-2xl">
                           Based on current liquidity of <span className="text-white">{formatCurrency(scorecard.total_cash)}</span> and average monthly burn of <span className="text-rose-500">{formatCurrency(scorecard.monthly_net_burn)}</span>.
                        </p>
                     </div>

                     <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <ProjectionStat label="Terminal Date" value={runway.zero_date} icon={Calendar} color="white" />
                        <ProjectionStat label="Confidence" value="92%" icon={Target} color="indigo" />
                        <ProjectionStat label="Monthly Burn" value={formatCurrency(scorecard.monthly_net_burn)} icon={TrendingDown} color="rose" />
                     </div>
                  </div>
               </div>
            </div>

            {/* Forecast Chart & Insights */}
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
               {/* Chart */}
               <div className="xl:col-span-8 glass-card rounded-[40px] p-10">
                  <div className="flex items-center justify-between mb-12">
                     <div>
                        <h3 className="text-xl font-black text-white font-outfit uppercase tracking-tighter">Liquidity Vector</h3>
                        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mt-1">6-Month Erosion Forecast</p>
                     </div>
                     <div className="bg-white/5 px-4 py-2 rounded-xl border border-white/5">
                        <div className="flex items-center gap-3">
                           <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.6)]" />
                           <span className="text-[9px] font-black uppercase tracking-widest text-slate-400 font-outfit">Active Reserves</span>
                        </div>
                     </div>
                  </div>

                  <div className="h-[380px] w-full mt-4">
                     <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={projectionData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                           <defs>
                              <linearGradient id="colorCash" x1="0" y1="0" x2="0" y2="1">
                                 <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                                 <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                              </linearGradient>
                           </defs>
                           <CartesianGrid strokeDasharray="10 10" vertical={false} stroke="rgba(255,255,255,0.02)" />
                           <XAxis
                              dataKey="month"
                              axisLine={false}
                              tickLine={false}
                              tick={{ fill: '#475569', fontSize: 10, fontWeight: 900 }}
                              dy={10}
                           />
                           <YAxis
                              axisLine={false}
                              tickLine={false}
                              tick={{ fill: '#475569', fontSize: 10, fontWeight: 900 }}
                              tickFormatter={(v) => `$${v / 1000}K`}
                           />
                           <Tooltip
                              contentStyle={{
                                 backgroundColor: '#020617',
                                 border: '1px solid rgba(255,255,255,0.1)',
                                 borderRadius: '20px',
                              }}
                              itemStyle={{ color: '#fff', fontSize: '11px', fontWeight: '900', textTransform: 'uppercase' }}
                           />
                           <Area
                              type="monotone"
                              dataKey="cash"
                              stroke="#6366f1"
                              strokeWidth={4}
                              fillOpacity={1}
                              fill="url(#colorCash)"
                              animationDuration={2500}
                           />
                        </AreaChart>
                     </ResponsiveContainer>
                  </div>
               </div>

               {/* Benchmarks */}
               <div className="xl:col-span-4 space-y-10">
                  <div className="bg-indigo-600 rounded-[40px] p-10 text-white relative overflow-hidden group shadow-[0_20px_50px_rgba(79,70,229,0.3)]">
                     <div className="absolute top-0 right-0 p-8 opacity-20 rotate-12 group-hover:rotate-45 transition-transform duration-1000">
                        <Sparkles className="w-20 h-20" />
                     </div>
                     <h3 className="text-xl font-black font-outfit tracking-tighter uppercase mb-6">Optimization Node</h3>
                     <p className="text-sm font-bold text-indigo-100 leading-relaxed opacity-90 mb-10">
                        Implementing a <span className="text-white font-black underline decoration-white/30">15% efficiency gain</span> in SaaS operations would extend terminal date to <span className="text-emerald-300 font-extrabold">MAR 2027</span>.
                     </p>
                     <div className="space-y-4">
                        <button className="w-full py-4 bg-white text-indigo-700 text-[10px] font-black uppercase tracking-[0.2em] rounded-2xl shadow-xl hover:bg-slate-50 transition-all active:scale-95">
                           Execute Simulation
                        </button>
                        <button className="w-full py-4 bg-white/10 hover:bg-white/20 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] transition-all border border-white/10 active:scale-95">
                           Protocol Details
                        </button>
                     </div>
                  </div>

                  <div className="glass-card rounded-[40px] p-10">
                     <h4 className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-500 mb-8 font-outfit">Compliance Matrix</h4>
                     <div className="space-y-6">
                        <CheckItem title="Fundraising Pack-01" status="SYNCED" color="emerald" />
                        <CheckItem title="Burn Optimization" status="ACTIVE" color="indigo" />
                        <CheckItem title="Vendor Logic" status="PENDING" color="slate" />
                     </div>
                  </div>
               </div>
            </div>
         </div>
      </div>
   );
}

function ProjectionStat({ label, value, icon: Icon, color = "indigo" }: any) {
   const colors: any = {
      indigo: "text-indigo-400",
      rose: "text-rose-400 shadow-[0_0_10px_rgba(244,63,94,0.3)]",
      white: "text-white",
   };

   return (
      <div className="space-y-3 bg-white/5 p-6 rounded-[30px] border border-white/5">
         <div className="flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">
            <Icon className="w-3.5 h-3.5" />
            <span>{label}</span>
         </div>
         <p className={cn("text-2xl font-black font-outfit tracking-tighter uppercase", colors[color])}>{value}</p>
      </div>
   );
}

function CheckItem({ title, status, color = "emerald" }: any) {
   const colors: any = {
      emerald: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20 shadow-[0_0_10px_rgba(52,211,153,0.1)]",
      indigo: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20 shadow-[0_0_10px_rgba(99,102,241,0.1)]",
      slate: "text-slate-500 bg-white/5 border-white/5 shadow-none",
   };

   return (
      <div className="flex items-center justify-between group p-1">
         <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest group-hover:text-white transition-colors">{title}</span>
         <span className={cn("px-3 py-1.5 rounded-xl text-[8px] font-black uppercase tracking-[0.2em] border transition-all group-hover:scale-105", colors[color])}>
            {status}
         </span>
      </div>
   );
}
