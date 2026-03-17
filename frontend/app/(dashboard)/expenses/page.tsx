"use client";

import TopBar from "@/components/TopBar";
import { useExpenses, useBurnRate } from "@/hooks/useFinancialData";
import { useAppStore } from "@/lib/store";
import { formatCurrency, formatCompactNumber, cn } from "@/lib/utils";
import {
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Receipt,
  Sparkles,
  Filter,
  Download,
  Search,
  Zap,
  Tag,
  Calendar,
  Layers,
  MoreVertical,
} from "lucide-react";

export default function ExpensesPage() {
  const { expenses, isLoading } = useExpenses();
  const { burnRate } = useBurnRate();
  const { openChat } = useAppStore();

  const totalExpenses = Object.values(expenses.breakdown as Record<string, number>).reduce((a: number, b: number) => a + b, 0);

  const categories = [
    { name: "Payroll", key: "payroll", color: "#6366f1", icon: "👥" },
    { name: "AWS", key: "aws", color: "#f97316", icon: "☁️" },
    { name: "SaaS", key: "saas", color: "#3b82f6", icon: "📦" },
    { name: "Marketing", key: "marketing", color: "#ec4899", icon: "📢" },
    { name: "Office", key: "office", color: "#22c55e", icon: "🏢" },
    { name: "Legal", key: "legal", color: "#a855f7", icon: "⚖️" },
  ];

  return (
    <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950/50 pb-12">
      <TopBar title="Capital Allocation" />

      <div className="p-8 space-y-8 max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
          <div className="space-y-1">
            <h1 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight font-outfit">
               Expenses
            </h1>
            <div className="flex items-center gap-2 text-slate-500 font-medium text-sm">
               <Layers className="w-4 h-4 text-indigo-500" />
               <span>Comprehensive breakdown of operational leakage</span>
               <span className="w-1 h-1 rounded-full bg-slate-300" />
               <span className="text-emerald-500 font-bold">Audit Ready</span>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
             <button className="flex items-center gap-2 px-5 py-3 text-sm font-bold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-all shadow-sm">
                <Download className="w-4 h-4" />
                Export
             </button>
             <button 
                onClick={() => openChat("Expense Leakage Audit")}
                className="flex items-center gap-2 px-6 py-3 text-sm font-bold text-white bg-indigo-600 rounded-2xl hover:bg-indigo-500 transition-all shadow-xl shadow-indigo-500/25 active:scale-95 group"
             >
                <Sparkles className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                Analyze Leakage
             </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
           <ExpenseStat 
              title="Total Outflow"
              value={formatCurrency(totalExpenses)}
              desc={`Trend: ${burnRate.trend}% vs last month`}
              icon={Receipt}
              status={burnRate.trend <= 0 ? "success" : "danger"}
           />
           <ExpenseStat 
              title="Largest Lever"
              value="Payroll"
              desc={`${formatCurrency(expenses.breakdown.payroll)} allocation`}
              icon={Tag}
              status="neutral"
           />
           <ExpenseStat 
              title="Velocity Peak"
              value={expenses.movers?.[0]?.category || "AWS"}
              desc={`+${expenses.movers?.[0]?.trend || 12.5}% shift`}
              icon={TrendingUp}
              status="danger"
           />
           <ExpenseStat 
              title="Annualized Burn"
              value={formatCurrency(totalExpenses * 12)}
              desc="Full year projection"
              icon={Calendar}
              status="neutral"
           />
        </div>

        {/* Main Content Sections */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
           
           {/* Expense Breakdown List */}
           <div className="xl:col-span-8 space-y-6">
              <div className="flex items-center justify-between">
                 <h2 className="text-xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">Category Intelligence</h2>
                 <div className="flex items-center gap-2">
                    <div className="relative group">
                       <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                       <input 
                          placeholder="Search categories..."
                          className="pl-9 pr-4 py-2 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 w-48 transition-all"
                       />
                    </div>
                 </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                 {categories.map((cat) => {
                   const amount = expenses.breakdown[cat.key] || 0;
                   const percentage = totalExpenses > 0 ? (amount / totalExpenses) * 100 : 0;
                   const trend = expenses.trend?.find((t) => t.category === cat.key)?.trend || 0;
                   
                   return (
                     <div
                       key={cat.key}
                       className="group p-6 bg-white dark:bg-slate-900/40 backdrop-blur-sm rounded-[32px] border border-slate-200 dark:border-slate-800/50 hover:border-indigo-500/30 hover:shadow-2xl hover:shadow-indigo-500/5 transition-all"
                     >
                       <div className="flex items-center justify-between mb-4">
                         <div className="flex items-center gap-4">
                           <div className="w-12 h-12 bg-slate-100 dark:bg-slate-800 rounded-2xl flex items-center justify-center text-xl transition-transform group-hover:scale-110 group-hover:bg-indigo-500/10 grayscale group-hover:grayscale-0">
                             {cat.icon}
                           </div>
                           <div>
                              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1 block">Category</span>
                              <span className="font-black text-slate-900 dark:text-white tracking-tight capitalize">
                                {cat.name}
                              </span>
                           </div>
                         </div>
                         <div className={cn(
                           "px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest border",
                           trend > 0 ? "text-rose-600 bg-rose-500/10 border-rose-500/20" : "text-emerald-600 bg-emerald-500/10 border-emerald-500/20"
                         )}>
                           {trend > 0 ? "+" : ""}{trend}%
                         </div>
                       </div>
                       
                       <div className="mt-4">
                          <p className="text-2xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">
                            {formatCurrency(amount)}
                          </p>
                          <div className="mt-4 space-y-2">
                             <div className="flex justify-between text-[10px] font-black uppercase tracking-widest text-slate-400">
                                <span>Utilization</span>
                                <span>{percentage.toFixed(1)}%</span>
                             </div>
                             <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden p-[2px] border border-slate-200/50 dark:border-slate-800/50">
                                <div
                                  className="h-full rounded-full transition-all duration-1000 group-hover:opacity-80 shadow-[0_0_10px_rgba(79,70,229,0.2)]"
                                  style={{ width: `${percentage}%`, backgroundColor: cat.color }}
                                />
                             </div>
                          </div>
                       </div>
                     </div>
                   );
                 })}
              </div>
           </div>

           {/* Side Activity */}
           <div className="xl:col-span-4 space-y-8">
              
              {/* Insight Card */}
              <div className="bg-indigo-600 rounded-[40px] p-8 text-white relative overflow-hidden group shadow-2xl shadow-indigo-500/20">
                 <div className="absolute -right-4 -bottom-4 opacity-[0.15] -rotate-12 transition-transform group-hover:-rotate-45 duration-1000">
                    <Sparkles className="w-48 h-48" />
                 </div>
                 
                 <div className="flex items-center gap-3 mb-8">
                    <div className="p-3 bg-white/20 rounded-2xl backdrop-blur-xl ring-1 ring-white/30">
                      <Zap className="w-5 h-5" />
                    </div>
                    <h2 className="text-xl font-black font-outfit tracking-tight">IA Insight</h2>
                 </div>
                 
                 <p className="text-sm font-bold leading-relaxed mb-8 relative z-10">
                    Cloud services (AWS) have increased by 12.5% this cycle. This correlates with the new deployment cycle. Recommend <span className="underline decoration-white/30">auto-scaling review</span>.
                 </p>
                 
                 <button onClick={() => openChat("Expense Audit: AWS Spike")} className="w-full py-4 bg-white text-indigo-700 font-black text-xs uppercase tracking-widest rounded-2xl hover:shadow-xl active:scale-[0.98] transition-all relative z-10">
                    Audit Vendor
                 </button>
              </div>

              {/* Transactions List */}
              <div className="glass-card rounded-[32px] p-8 border border-slate-200 dark:border-slate-800/50">
                 <div className="flex items-center justify-between mb-8">
                    <h3 className="text-lg font-black text-slate-900 dark:text-white font-outfit tracking-tight">Recent outflow</h3>
                    <MoreVertical className="w-4 h-4 text-slate-400" />
                 </div>
                 
                 <div className="space-y-6">
                   {[
                     { vendor: "AWS", category: "Cloud", date: "Mar 15", amount: 8450, icon: "☁️" },
                     { vendor: "WeWork", category: "Office", date: "Mar 14", amount: 2500, icon: "🏢" },
                     { vendor: "Figma", category: "SaaS", date: "Mar 13", amount: 525, icon: "📦" },
                     { vendor: "Google", category: "Cloud", date: "Mar 12", amount: 2100, icon: "☁️" },
                     { vendor: "Gusto", category: "Payroll", date: "Mar 10", amount: 42000, icon: "👥" },
                   ].map((tx, i) => (
                     <div
                       key={i}
                       className="flex items-center justify-between group cursor-default"
                     >
                       <div className="flex items-center gap-4">
                         <div className="w-10 h-10 bg-slate-100 dark:bg-slate-800 rounded-xl flex items-center justify-center text-lg transition-transform group-hover:scale-110">
                           {tx.icon}
                         </div>
                         <div>
                           <p className="text-sm font-black text-slate-900 dark:text-white tracking-tight">{tx.vendor}</p>
                           <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-0.5">{tx.category} • {tx.date}</p>
                         </div>
                       </div>
                       <p className="text-sm font-black text-slate-900 dark:text-white font-outfit">
                         {formatCompactNumber(tx.amount)}
                       </p>
                     </div>
                   ))}
                 </div>
                 
                 <button className="w-full mt-10 py-4 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-slate-900 dark:hover:text-white bg-slate-100/50 dark:bg-slate-900/50 rounded-2xl transition-all border border-slate-200/50 dark:border-slate-800/50">
                    Full Ledger Log
                 </button>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}

function ExpenseStat({ title, value, desc, icon: Icon, status }: any) {
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
