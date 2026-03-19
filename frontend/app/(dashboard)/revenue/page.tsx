"use client";

import TopBar from "@/components/TopBar";
import { useRevenue, useScorecard } from "@/hooks/useFinancialData";
import { useAppStore } from "@/lib/store";
import { formatCurrency, formatCompactNumber, cn } from "@/lib/utils";
import {
   TrendingUp,
   TrendingDown,
   ArrowUpRight,
   ArrowDownRight,
   DollarSign,
   Users,
   Repeat,
   Sparkles,
   CreditCard,
   Building2,
   LineChart,
   Target,
   ArrowRight,
   PieChart,
   Zap,
} from "lucide-react";
import {
   BarChart,
   Bar,
   XAxis,
   YAxis,
   CartesianGrid,
   Tooltip,
   ResponsiveContainer,
   Cell,
   PieChart as RechartsPieChart,
   Pie,
} from "recharts";

const mrrHistory = [
   { month: "Oct", value: 38000 },
   { month: "Nov", value: 39500 },
   { month: "Dec", value: 41000 },
   { month: "Jan", value: 42500 },
   { month: "Feb", value: 44000 },
   { month: "Mar", value: 45000 },
];

const revenueMix = [
   { name: "Subscription", value: 38500, color: "#4f46e5" },
   { name: "Usage", value: 4500, color: "#a855f7" },
   { name: "Services", value: 2000, color: "#10b981" },
];

export default function RevenuePage() {
   const { revenue, isLoading } = useRevenue();
   const { scorecard } = useScorecard();
   const { openChat } = useAppStore();

   return (
      <div className="min-h-screen bg-slate-950 pb-20">
         <TopBar title="Revenue Intelligence" />

         <div className="p-8 space-y-10 max-w-[1600px] mx-auto">
            {/* Header Section */}
            <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8">
               <div className="space-y-4">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-bold uppercase tracking-wider">
                     <LineChart className="w-3.5 h-3.5" />
                     Growth Performance Active
                  </div>
                  <h1 className="text-4xl font-black text-white tracking-tight font-outfit uppercase">
                     Revenue <span className="text-slate-500">Analytics</span>
                  </h1>
                  <div className="flex items-center gap-4 text-slate-500 font-bold text-[10px] uppercase tracking-widest">
                     <div className="flex items-center gap-2">
                        <Target className="w-3.5 h-3.5" />
                        <span>Projected MRR: {formatCurrency(revenue.mrr * 1.1)}</span>
                     </div>
                     <div className="w-1.5 h-1.5 rounded-full bg-slate-800" />
                     <div className="flex items-center gap-2 text-emerald-500">
                        <TrendingUp className="w-3.5 h-3.5" />
                        <span>Market Status: SECURE</span>
                     </div>
                  </div>
               </div>

               <button
                  onClick={() => openChat("Revenue growth strategy")}
                  className="btn-secondary text-xs"
               >
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  Run Strategy Audit
               </button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
               {[
                  { title: "Current MRR", value: formatCurrency(revenue.mrr), icon: DollarSign, trend: `+${revenue.growth_pct}%`, trendColor: "text-emerald-500" },
                  { title: "Projected ARR", value: formatCurrency(revenue.arr), icon: Building2, trend: "Target Match", trendColor: "text-slate-400" },
                  { title: "Net Retention", value: `${revenue.nrr}%`, icon: Repeat, trend: "Strong", trendColor: "text-indigo-400" },
                  { title: "Logo Churn", value: `${revenue.churn_rate}%`, icon: TrendingDown, trend: "-0.2%", trendColor: "text-emerald-500" },
               ].map((stat, i) => (
                  <div key={i} className="bg-slate-900 border border-white/10 p-6 rounded-2xl group hover:border-indigo-500/30 transition-all">
                     <div className="flex items-center justify-between mb-4">
                        <div className="p-2 rounded-lg bg-white/5 text-slate-400 group-hover:text-indigo-400 transition-colors">
                           <stat.icon className="w-5 h-5" />
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider ${stat.trendColor}`}>{stat.trend}</span>
                     </div>
                     <div className="space-y-1">
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{stat.title}</span>
                        <div className="text-2xl font-black text-white font-outfit uppercase tracking-tight">{stat.value}</div>
                     </div>
                  </div>
               ))}
            </div>

            {/* Breakdown Section */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
               {/* MRR Trend Chart */}
               <div className="lg:col-span-8 bg-slate-900 border border-white/10 rounded-3xl p-8">
                  <div className="flex items-center justify-between mb-8">
                     <div>
                        <h2 className="text-xl font-bold text-white font-outfit uppercase tracking-tighter">Growth Trajectory</h2>
                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-0.5">Monthly Recurring Revenue Matrix</p>
                     </div>
                     <div className="flex items-center gap-2 px-3 py-1 bg-slate-950 rounded-lg border border-white/5">
                        <div className="w-2 h-2 rounded-full bg-indigo-500" />
                        <span className="text-[10px] font-bold uppercase text-slate-400">Standard Growth</span>
                     </div>
                  </div>

                  <div className="h-[350px] w-full">
                     <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={mrrHistory} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
                           <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                           <XAxis
                              dataKey="month"
                              axisLine={false}
                              tickLine={false}
                              tick={{ fill: '#64748b', fontSize: 11, fontWeight: 700 }}
                           />
                           <YAxis
                              axisLine={false}
                              tickLine={false}
                              tick={{ fill: '#64748b', fontSize: 11, fontWeight: 700 }}
                              tickFormatter={(v) => `$${v / 1000}K`}
                           />
                           <Tooltip
                              cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                              contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                           />
                           <Bar dataKey="value" fill="#6366f1" radius={[8, 8, 2, 2]} barSize={40}>
                              {mrrHistory.map((entry, index) => (
                                 <Cell
                                    key={`cell-${index}`}
                                    fill={index === mrrHistory.length - 1 ? '#6366f1' : '#1e293b'}
                                 />
                              ))}
                           </Bar>
                        </BarChart>
                     </ResponsiveContainer>
                  </div>
               </div>

               {/* Revenue Mix */}
               <div className="lg:col-span-4 flex flex-col gap-8">
                  <div className="bg-slate-900 border border-white/10 rounded-3xl p-8 flex-1">
                     <h3 className="text-lg font-bold text-white font-outfit uppercase tracking-tight mb-8">Segment Mix</h3>
                     <div className="h-[200px] w-full relative mb-8">
                        <ResponsiveContainer width="100%" height="100%">
                           <RechartsPieChart>
                              <Pie
                                 data={revenueMix}
                                 cx="50%"
                                 cy="50%"
                                 innerRadius={65}
                                 outerRadius={85}
                                 paddingAngle={8}
                                 dataKey="value"
                                 stroke="none"
                              >
                                 {revenueMix.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                 ))}
                              </Pie>
                              <Tooltip />
                           </RechartsPieChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                           <span className="text-2xl font-black text-white font-outfit">100%</span>
                        </div>
                     </div>
                     <div className="space-y-4">
                        {revenueMix.map((item) => (
                           <div key={item.name} className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                 <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                                 <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{item.name}</span>
                              </div>
                              <span className="text-xs font-bold text-white uppercase">{((item.value / 45000) * 100).toFixed(0)}%</span>
                           </div>
                        ))}
                     </div>
                  </div>

                  {/* Expansion Node Card */}
                  <div className="bg-indigo-600 rounded-3xl p-8 text-white relative overflow-hidden group">
                     <Zap className="absolute -right-8 -bottom-8 w-40 h-40 opacity-10 rotate-12" />
                     <h2 className="text-xl font-black font-outfit uppercase tracking-tight mb-4 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5" />
                        Growth Engine
                     </h2>
                     <p className="text-sm font-medium leading-relaxed mb-8 opacity-90">
                        Usage metrics suggest a 14% efficiency gap. Recommended shift to tiered scaling.
                     </p>
                     <button
                        onClick={() => openChat("Tiered scaling model")}
                        className="w-full py-4 bg-white text-indigo-700 text-[10px] font-black uppercase tracking-[0.2em] rounded-xl hover:bg-slate-100 transition-all shadow-lg font-outfit"
                     >
                        Execute Simulator
                     </button>
                  </div>
               </div>
            </div>

            {/* Specialized Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
               <MetricBox
                  title="Expansion Rate"
                  value={`${revenue.nrr}%`}
                  desc="Upsell performance"
                  icon={Repeat}
                  color="indigo"
               />
               <MetricBox
                  title="Customer LTV"
                  value="$18.5K"
                  desc="Projected lifetime"
                  icon={Users}
                  color="purple"
               />
               <MetricBox
                  title="CAC Protocol"
                  value="$2.4K"
                  desc="Acquisition efficiency"
                  icon={CreditCard}
                  color="emerald"
               />
            </div>
         </div>
      </div>
   );
}

function MetricBox({ title, value, desc, icon: Icon, color }: any) {
   const colorStyles: any = {
      indigo: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
      purple: "text-purple-400 bg-purple-500/10 border-purple-500/20",
      emerald: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
   };

   return (
      <div className="glass-card rounded-[40px] p-10 flex flex-col items-center text-center group hover:bg-white/[0.03] transition-all duration-500">
         <div className={cn("p-6 rounded-3xl mb-8 transition-all duration-500 group-hover:scale-110 group-hover:rotate-6 shadow-2xl border", colorStyles[color])}>
            <Icon className="w-10 h-10" />
         </div>
         <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-3">{title}</p>
         <h3 className="text-4xl font-black text-white font-outfit tracking-tighter mb-4 uppercase">{value}</h3>
         <p className="text-xs font-bold text-slate-600 uppercase tracking-widest">{desc}</p>
         <button className="mt-10 py-3 px-6 text-[9px] font-black text-white bg-white/5 border border-white/5 rounded-xl opacity-0 group-hover:opacity-100 transition-all uppercase tracking-[0.2em] hover:bg-white/10 active:scale-95">
            Deep Analysis Node <ArrowRight className="w-3 h-3 inline-block ml-2" />
         </button>
      </div>
   );
}

function RevenueStat({ title, value, desc, icon: Icon, status }: any) {
   const statusStyles: any = {
      success: "bg-emerald-500/10 text-emerald-500",
      danger: "bg-rose-500/10 text-rose-500",
      warning: "bg-amber-500/10 text-amber-500",
      neutral: "bg-indigo-500/10 text-indigo-500",
   };

   return (
      <div className="bg-white dark:bg-slate-900/40 backdrop-blur-sm rounded-[32px] border border-slate-200 dark:border-slate-800/50 p-6 group transition-all hover:border-indigo-500/20">
         <div className="flex items-start justify-between">
            <div className={cn("p-4 rounded-2xl transition-transform group-hover:scale-110", statusStyles[status])}>
               <Icon className="w-6 h-6" />
            </div>
         </div>
         <div className="mt-5">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{title}</p>
            <h2 className="text-3xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">{value}</h2>
            <p className="text-xs font-bold text-slate-500 mt-2">{desc}</p>
         </div>
      </div>
   );
}


