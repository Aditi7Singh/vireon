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
    ? { label: "Critical", color: "text-rose-500", bg: "bg-rose-500/10", icon: AlertTriangle }
    : isHealthyRunway 
      ? { label: "Stable", color: "text-emerald-500", bg: "bg-emerald-500/10", icon: Shield }
      : { label: "Guarded", color: "text-amber-500", bg: "bg-amber-500/10", icon: Clock };

  return (
    <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950/50 pb-12">
      <TopBar title="Survival Analysis" />

      <div className="p-8 space-y-8 max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
          <div className="space-y-1">
            <h1 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight font-outfit">
               Runway
            </h1>
            <div className="flex items-center gap-2 text-slate-500 font-medium text-sm">
               <Clock className="w-4 h-4 text-indigo-500" />
               <span>Time-to-zero projected from operational churn</span>
               <span className="w-1 h-1 rounded-full bg-slate-300" />
               <span className={cn("font-bold uppercase tracking-widest text-[10px]", runwayStatus.color)}>Status: {runwayStatus.label}</span>
            </div>
          </div>
          
          <button 
             onClick={openChat}
             className="flex items-center gap-2 px-6 py-3 text-sm font-bold text-white bg-indigo-600 rounded-2xl hover:bg-indigo-500 transition-all shadow-xl shadow-indigo-500/25 active:scale-95 group"
          >
             <Zap className="w-4 h-4" />
             Capital Strategy Chat
          </button>
        </div>

        {/* Central Display */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
           
           {/* Life Clock Hero */}
           <div className="xl:col-span-12 glass-card rounded-[40px] p-10 border border-slate-200 dark:border-slate-800/50 relative overflow-hidden">
               <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
                  <Waves className="w-64 h-64 -rotate-12" />
               </div>
               
               <div className="flex flex-col lg:flex-row lg:items-center gap-12 relative z-10">
                  <div className="flex-shrink-0 relative">
                     <div className={cn("w-48 h-48 rounded-full flex flex-col items-center justify-center border-8 transition-colors duration-1000", 
                       isLowRunway ? "border-rose-500/20 shadow-[0_0_30px_rgba(244,63,94,0.1)]" : "border-indigo-500/10 shadow-[0_0_30px_rgba(99,102,241,0.1)]")}>
                        <span className={cn("text-7xl font-black font-outfit tracking-tighter leading-none mb-1", runwayStatus.color)}>
                           {runway.runway_months}
                        </span>
                        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Months</span>
                     </div>
                     <div className={cn("absolute -bottom-2 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-xl border flex items-center gap-2 shadow-xl", runwayStatus.bg, "border-white/20 backdrop-blur-md")}>
                        <runwayStatus.icon className={cn("w-3.5 h-3.5", runwayStatus.color)} />
                        <span className={cn("text-[10px] font-black uppercase tracking-widest", runwayStatus.color)}>{runwayStatus.label}</span>
                     </div>
                  </div>

                  <div className="flex-grow space-y-6">
                     <div>
                        <h2 className="text-3xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">Depletion Projection</h2>
                        <p className="text-slate-500 font-medium max-w-xl">
                           Based on current liquidity of <span className="text-slate-900 dark:text-white font-bold">{formatCurrency(scorecard.total_cash)}</span> and an average monthly burn of <span className="text-rose-500 font-bold">{formatCurrency(scorecard.monthly_net_burn)}</span>.
                        </p>
                     </div>
                     
                     <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                        <ProjectionStat label="Zero Cash Date" value={runway.zero_date} icon={Calendar} />
                        <ProjectionStat label="Confidence" value={runway.confidence_interval} icon={Target} />
                        <ProjectionStat label="Monthly Leak" value={formatCurrency(scorecard.monthly_net_burn)} icon={TrendingDown} color="rose" />
                     </div>
                  </div>
               </div>
           </div>

           {/* Forecast Chart */}
           <div className="xl:col-span-8 glass-card rounded-[32px] p-8">
              <div className="flex items-center justify-between mb-8">
                <div>
                   <h3 className="text-xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">Cash Velocity Forecast</h3>
                   <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">6-Month Liquidity Path</p>
                </div>
                <div className="flex items-center gap-4">
                   <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-indigo-500/20 border border-indigo-500" />
                      <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Cash Reserves</span>
                   </div>
                </div>
              </div>

              <div className="h-[320px] w-full mt-4">
                 <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={projectionData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                       <defs>
                          <linearGradient id="colorCash" x1="0" y1="0" x2="0" y2="1">
                             <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.1}/>
                             <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                          </linearGradient>
                       </defs>
                       <XAxis 
                         dataKey="month" 
                         axisLine={false} 
                         tickLine={false} 
                         tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 700 }}
                         dy={10}
                       />
                       <YAxis 
                         axisLine={false} 
                         tickLine={false} 
                         tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 700 }}
                         tickFormatter={(v) => `$${v/1000}k`}
                       />
                       <Tooltip 
                         contentStyle={{ 
                           backgroundColor: '#0f172a', 
                           border: 'none', 
                           borderRadius: '16px',
                           boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)'
                         }}
                         itemStyle={{ color: '#fff', fontSize: '12px', fontWeight: 'bold' }}
                       />
                       <Area 
                         type="monotone" 
                         dataKey="cash" 
                         stroke="#4f46e5" 
                         strokeWidth={4}
                         fillOpacity={1} 
                         fill="url(#colorCash)" 
                         animationDuration={2000}
                       />
                    </AreaChart>
                 </ResponsiveContainer>
              </div>
           </div>

           {/* Strategy Bench */}
           <div className="xl:col-span-4 space-y-6">
              <div className="bg-slate-900 rounded-[32px] p-8 text-white relative overflow-hidden group shadow-2xl">
                 <div className="absolute top-0 right-0 p-6 opacity-20 rotate-12 group-hover:rotate-45 transition-transform duration-700">
                    <Sparkles className="w-12 h-12" />
                 </div>
                 <h3 className="text-lg font-black font-outfit tracking-tight mb-4">Strategic Leak Recovery</h3>
                 <p className="text-xs text-slate-400 leading-relaxed mb-8">
                    Implementing a <span className="text-white font-bold">15% reduction</span> in SaaS waste would extend runway to <span className="text-emerald-400 font-bold">Nov 2026</span>.
                 </p>
                 <div className="space-y-3">
                    <button className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all">
                       Simulate scenario
                    </button>
                    <button className="w-full py-3 bg-white/5 hover:bg-white/10 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all border border-white/10">
                       Review SaaS waste
                    </button>
                 </div>
              </div>

              <div className="glass-card rounded-[32px] p-8 border border-slate-200 dark:border-slate-800/50">
                 <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-6">Survival Checklist</h4>
                 <div className="space-y-4">
                    <CheckItem title="Fundraising Pack-01" status="Complete" />
                    <CheckItem title="Burn-Rate Optimization" status="In Progress" color="indigo" />
                    <CheckItem title="Vendor Negotiation" status="Pending" color="slate" />
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
    indigo: "text-indigo-600 dark:text-indigo-400",
    rose: "text-rose-600 dark:text-rose-400",
  };

  return (
    <div className="space-y-1">
       <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest text-slate-400">
          <Icon className="w-3 h-3" />
          <span>{label}</span>
       </div>
       <p className={cn("text-xl font-black font-outfit", colors[color])}>{value}</p>
    </div>
  );
}

function CheckItem({ title, status, color = "emerald" }: any) {
  const colors: any = {
    emerald: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    indigo: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20",
    slate: "bg-slate-500/10 text-slate-400 border-slate-500/20",
  };

  return (
    <div className="flex items-center justify-between group">
       <span className="text-sm font-bold text-slate-700 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">{title}</span>
       <span className={cn("px-2.5 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest border", colors[color])}>
          {status}
       </span>
    </div>
  );
}
