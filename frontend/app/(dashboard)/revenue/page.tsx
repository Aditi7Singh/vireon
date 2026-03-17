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
    <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950/50 pb-12">
      <TopBar title="Revenue Intelligence" />

      <div className="p-8 space-y-8 max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
          <div className="space-y-1">
            <h1 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight font-outfit">
               Revenue 
            </h1>
            <div className="flex items-center gap-2 text-slate-500 font-medium text-sm">
               <LineChart className="w-4 h-4 text-indigo-500" />
               <span>Performance monitoring at scale</span>
               <span className="w-1 h-1 rounded-full bg-slate-300" />
               <span className="text-emerald-500 font-bold">Growth Neutral</span>
            </div>
          </div>
          
          <button 
             onClick={() => openChat("Revenue Intelligence")}
             className="flex items-center gap-2 px-6 py-3 text-sm font-bold text-white bg-indigo-600 rounded-2xl hover:bg-indigo-500 transition-all shadow-xl shadow-indigo-500/25 active:scale-95 group"
          >
             <Sparkles className="w-4 h-4 group-hover:rotate-12 transition-transform" />
             Strategic Growth Audit
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
           <RevenueStat 
              title="Current MRR"
              value={formatCurrency(revenue.mrr)}
              desc={`+${revenue.growth_pct}% vs Prev. Month`}
              icon={DollarSign}
              status="success"
           />
           <RevenueStat 
              title="Annualized RR"
              value={formatCurrency(revenue.arr)}
              desc="Based on current momentum"
              icon={Building2}
              status="neutral"
           />
           <RevenueStat 
              title="Growth Vector"
              value={`+${revenue.growth_pct}%`}
              desc="Projected Trend line"
              icon={TrendingUp}
              status="success"
           />
           <RevenueStat 
              title="Gross Churn"
              value={`${revenue.churn_rate}%`}
              desc="Logo retention focus"
              icon={TrendingDown}
              status="warning"
           />
        </div>

        {/* Breakdown Section */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* MRR Trend Chart */}
          <div className="lg:col-span-8 glass-card rounded-[32px] p-8 border border-slate-200 dark:border-slate-800/50">
             <div className="flex items-center justify-between mb-8">
               <div>
                  <h2 className="text-xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">MRR Progression</h2>
                  <p className="text-sm text-slate-500 font-medium">Historical trajectory (Last 6 months)</p>
               </div>
               <div className="p-3 bg-indigo-500/10 rounded-2xl">
                  <LineChart className="w-5 h-5 text-indigo-600" />
               </div>
             </div>
             
             <div className="h-[340px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                   <BarChart data={mrrHistory} margin={{ top: 20, right: 0, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.5} />
                      <XAxis 
                        dataKey="month" 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 700 }}
                        dy={15}
                      />
                      <YAxis 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 700 }}
                        tickFormatter={(v) => `$${v/1000}k`}
                      />
                      <Tooltip 
                        cursor={{ fill: '#f1f5f9', radius: 8 }}
                        contentStyle={{ 
                          backgroundColor: '#0f172a', 
                          border: 'none', 
                          borderRadius: '16px',
                          boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)'
                        }}
                        itemStyle={{ color: '#fff', fontSize: '12px', fontWeight: 'bold' }}
                      />
                      <Bar dataKey="value" fill="#4f46e5" radius={[12, 12, 4, 4]} barSize={40}>
                         {mrrHistory.map((entry, index) => (
                           <Cell 
                             key={`cell-${index}`} 
                             fill={index === mrrHistory.length - 1 ? '#4f46e5' : '#e2e8f0'} 
                             fillOpacity={index === mrrHistory.length - 1 ? 1 : 0.4}
                           />
                         ))}
                      </Bar>
                   </BarChart>
                </ResponsiveContainer>
             </div>
          </div>

          {/* Revenue Mix */}
          <div className="lg:col-span-4 space-y-8">
             <div className="glass-card rounded-[32px] p-8">
                <h3 className="text-lg font-black text-slate-900 dark:text-white font-outfit tracking-tight mb-8 text-center">Portfolio Mix</h3>
                
                <div className="h-[220px] w-full relative">
                   <ResponsiveContainer width="100%" height="100%">
                      <RechartsPieChart>
                         <Pie
                           data={revenueMix}
                           cx="50%"
                           cy="50%"
                           innerRadius={70}
                           outerRadius={90}
                           paddingAngle={8}
                           dataKey="value"
                         >
                           {revenueMix.map((entry, index) => (
                             <Cell key={`cell-${index}`} fill={entry.color} />
                           ))}
                         </Pie>
                         <Tooltip />
                      </RechartsPieChart>
                   </ResponsiveContainer>
                   <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                      <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none">Total</span>
                      <span className="text-2xl font-black text-slate-900 dark:text-white font-outfit tracking-tighter">100%</span>
                   </div>
                </div>

                <div className="mt-8 space-y-4">
                   {revenueMix.map((item) => (
                     <div key={item.name} className="flex items-center justify-between group">
                        <div className="flex items-center gap-3">
                           <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                           <span className="text-xs font-black text-slate-700 dark:text-slate-300 uppercase tracking-widest">{item.name}</span>
                        </div>
                        <span className="text-sm font-black text-slate-900 dark:text-white">{((item.value / 45000) * 100).toFixed(1)}%</span>
                     </div>
                   ))}
                </div>
             </div>
             
             {/* AI Insight Card */}
             <div className="bg-indigo-600 rounded-[32px] p-8 text-white relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-6 opacity-20">
                   <Zap className="w-12 h-12" />
                </div>
                <p className="text-[10px] font-black uppercase tracking-widest text-indigo-200 mb-2">Expansion Opportunity</p>
                <p className="text-sm font-bold leading-relaxed mb-6 group-hover:translate-x-1 transition-transform">
                   Usage-based revenue grew <span className="text-emerald-300 underline underline-offset-4 decoration-emerald-300/30">14% faster</span> than subscriptions. Recommend tiered scaling.
                </p>
                <button 
                  onClick={() => openChat("Revenue Expansion Opportunity")}
                  className="w-full py-3 bg-white/10 hover:bg-white/20 backdrop-blur-md rounded-2xl text-xs font-black uppercase tracking-widest transition-all border border-white/10"
                >
                   Model Tiers
                </button>
             </div>
          </div>
        </div>

        {/* Specialized Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
           <MetricBox 
              title="Net Revenue Retention"
              value={`${revenue.nrr}%`}
              desc="Health of existing user base"
              icon={Repeat}
              color="indigo"
           />
           <MetricBox 
              title="Avg. Customer LTV"
              value="$18,500"
              desc="Lifetime value per logo"
              icon={Users}
              color="purple"
           />
           <MetricBox 
              title="Avg. CAC"
              value="$2,400"
              desc="Customer acquisition cost"
              icon={CreditCard}
              color="emerald"
           />
        </div>
      </div>
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

function MetricBox({ title, value, desc, icon: Icon, color }: any) {
  const colorStyles: any = {
    indigo: "text-indigo-600 bg-indigo-50 dark:bg-indigo-500/10",
    purple: "text-purple-600 bg-purple-50 dark:bg-purple-500/10",
    emerald: "text-emerald-600 bg-emerald-50 dark:bg-emerald-500/10",
  };

  return (
    <div className="glass-card rounded-[32px] p-8 border border-slate-200 dark:border-slate-800/50 flex flex-col items-center text-center group">
       <div className={cn("p-4 rounded-[20px] mb-6 transition-transform group-hover:scale-110", colorStyles[color])}>
          <Icon className="w-8 h-8" />
       </div>
       <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">{title}</p>
       <h3 className="text-3xl font-black text-slate-900 dark:text-white font-outfit tracking-tight mb-2">{value}</h3>
       <p className="text-xs font-medium text-slate-500">{desc}</p>
       <button className="mt-6 text-[10px] font-black text-indigo-600 dark:text-indigo-400 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all uppercase tracking-widest">
          Details <ArrowRight className="w-3 h-3" />
       </button>
    </div>
  );
}
