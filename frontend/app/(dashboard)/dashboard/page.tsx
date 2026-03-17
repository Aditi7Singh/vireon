"use client";

import { useEffect } from "react";
import TopBar from "@/components/TopBar";
import { KpiCard } from "@/components/kpi/KpiCard";
import { useAppStore } from "@/lib/store";
import { useScorecard, useAlerts, useBurnRate, useRevenue } from "@/hooks/useFinancialData";
import { formatCurrency, formatCompactNumber, getRunwayStatus, formatRelativeTime, cn } from "@/lib/utils";
import {
  DollarSign,
  TrendingUp,
  Calendar,
  Users,
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
  Zap,
  Bot,
  Plus,
  Download,
  MoreHorizontal,
  ChevronRight,
  Sparkles,
  Target,
  Clock,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from "recharts";

// Mock chart data for visualization
const chartData = [
  { date: "Oct", Revenue: 21000, Expenses: 18000 },
  { date: "Nov", Revenue: 23500, Expenses: 19500 },
  { date: "Dec", Revenue: 27000, Expenses: 22000 },
  { date: "Jan", Revenue: 31000, Expenses: 24000 },
  { date: "Feb", Revenue: 38000, Expenses: 28000 },
  { date: "Mar", Revenue: 45000, Expenses: 32000 },
];

const recentTransactions = [
  { id: 1, name: "Stripe Processing", amount: -1240, date: "Today, 2:45 PM", category: "saas" },
  { id: 2, name: "Annual Retainer - Acme Corp", amount: 45000, date: "Yesterday, 10:15 AM", category: "revenue" },
  { id: 3, name: "Amazon Web Services", amount: -4821, date: "Mar 14, 11:30 PM", category: "aws" },
  { id: 4, name: "Gusto Payroll", amount: -28500, date: "Mar 12, 9:00 AM", category: "payroll" },
  { id: 5, name: "Google Cloud Platform", amount: -3200, date: "Mar 10, 4:20 PM", category: "aws" },
];

export default function DashboardPage() {
  const { openChat, setAlertCount, setCriticalAlertCount } = useAppStore();
  const { scorecard, isLoading: scorecardLoading } = useScorecard();
  const { alerts, isLoading: alertsLoading } = useAlerts();
  const { burnRate, isLoading: burnLoading } = useBurnRate();
  const { revenue, isLoading: revenueLoading } = useRevenue();

  // Update global state in useEffect
  useEffect(() => {
    if (alerts) {
      setAlertCount(alerts.total);
      setCriticalAlertCount(alerts.critical_count);
    }
  }, [alerts, setAlertCount, setCriticalAlertCount]);

  const runwayStatus = getRunwayStatus(scorecard.runway_months);

  const handleConsultAI = () => {
    openChat("Financial Dashboard");
  };

  return (
    <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950/50 pb-12">
      <TopBar title="Financial Command Center" />
      
      <div className="p-8 space-y-8 max-w-[1600px] mx-auto">
        {/* Hero Section / Welcome */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2 mb-2">
               <span className="px-3 py-1 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 text-[10px] font-black uppercase tracking-widest rounded-full border border-indigo-500/20">Alpha Intelligence</span>
            </div>
            <h1 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight font-outfit">
               Dashboard
            </h1>
            <div className="flex items-center gap-2 text-slate-500 font-medium text-sm">
               <Clock className="w-4 h-4" />
               <span>Last intelligence update: Just now</span>
               <span className="w-1 h-1 rounded-full bg-slate-300" />
               <span className="text-emerald-500 font-bold">Live ERP Connection</span>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
             <button className="flex items-center gap-2 px-5 py-3 text-sm font-bold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-all shadow-sm">
                <Download className="w-4 h-4" />
                Export Data
             </button>
             <button 
                onClick={handleConsultAI}
                className="flex items-center gap-2 px-6 py-3 text-sm font-bold text-white bg-indigo-600 rounded-2xl hover:bg-indigo-500 transition-all shadow-xl shadow-indigo-500/25 active:scale-95 group"
             >
                <Bot className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                Consult AI CFO
             </button>
          </div>
        </div>

        {/* KPI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KpiCard
            title="Total Liquidity"
            value={formatCurrency(scorecard.total_cash)}
            change={12.5}
            icon={DollarSign}
            status="healthy"
          />
          <KpiCard
            title="Burn Velocity"
            value={formatCurrency(scorecard.monthly_gross_burn)}
            change={-4.2}
            icon={TrendingUp}
            status="warning"
          />
          <KpiCard
            title="Capital Runway"
            value={`${scorecard.runway_months} Mo`}
            change={2.1}
            icon={Calendar}
            status={scorecard.runway_months >= 18 ? "healthy" : scorecard.runway_months >= 9 ? "warning" : "critical"}
          />
          <KpiCard
            title="Monthly Revenue"
            value={formatCurrency(scorecard.monthly_revenue)}
            change={revenue.growth_pct}
            icon={Users}
            status="healthy"
          />
        </div>

        {/* Main Intelligence Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
          {/* Detailed Analytics - 8 cols */}
          <div className="xl:col-span-8 space-y-8">
            
            {/* Cash Flow Intelligence */}
            <div className="glass-card rounded-[32px] p-8 relative overflow-hidden">
               <div className="absolute top-0 right-0 p-8 opacity-[0.03] dark:opacity-[0.07]">
                  <TrendingUp className="w-32 h-32" />
               </div>
               
               <div className="flex items-center justify-between mb-8">
                 <div>
                   <h2 className="text-xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">
                     Cash Dynamics
                   </h2>
                   <p className="text-sm text-slate-500 font-medium">Monthly inflow vs outflow analysis</p>
                 </div>
                 <div className="flex items-center gap-4 bg-slate-100 dark:bg-slate-900/50 p-1.5 rounded-2xl border border-slate-200/50 dark:border-slate-800/50">
                   <button className="px-4 py-1.5 text-[10px] font-black uppercase tracking-widest bg-white dark:bg-slate-800 rounded-xl shadow-sm">6 Months</button>
                   <button className="px-4 py-1.5 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-slate-900 dark:hover:text-slate-300 transition-colors">1 Year</button>
                 </div>
               </div>
               
               {/* Real Area Chart with Recharts */}
               <div className="h-[360px] w-full mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorExpenses" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.1}/>
                          <stop offset="95%" stopColor="#94a3b8" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.5} />
                      <XAxis 
                        dataKey="date" 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 700 }}
                        dy={15}
                      />
                      <YAxis 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 700 }}
                        tickFormatter={(value) => `$${value/1000}k`}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                          border: 'none', 
                          borderRadius: '16px',
                          color: '#fff',
                          boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)'
                        }}
                        itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="Revenue" 
                        stroke="#4f46e5" 
                        strokeWidth={4}
                        fillOpacity={1} 
                        fill="url(#colorRevenue)" 
                        animationDuration={2000}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="Expenses" 
                        stroke="#94a3b8" 
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        fillOpacity={1} 
                        fill="url(#colorExpenses)" 
                      />
                    </AreaChart>
                  </ResponsiveContainer>
               </div>
            </div>

            {/* Bottom Row: Runway + Expenses */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
               {/* Runway Health */}
               <div className="glass-card rounded-[32px] p-8 relative overflow-hidden group">
                  <div className="flex items-center justify-between mb-8">
                     <div>
                        <h3 className="text-lg font-black text-slate-900 dark:text-white font-outfit tracking-tight">Runway Efficiency</h3>
                        <p className="text-xs text-slate-500 font-medium">Sustainability forecast</p>
                     </div>
                     <div className={cn("px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border", runwayStatus.bgColor, runwayStatus.color, "border-current/20")}>
                        {runwayStatus.label}
                     </div>
                  </div>
                  
                  <div className="relative pt-4">
                     <div className="flex justify-between text-[10px] font-black uppercase tracking-widest mb-3">
                        <span className="text-slate-400">Resource Utilization</span>
                        <span className="text-slate-900 dark:text-white">{Math.min(100, (scorecard.runway_months / 18) * 100).toFixed(0)}%</span>
                     </div>
                     <div className="h-5 bg-slate-100 dark:bg-slate-900 rounded-2xl overflow-hidden p-1 border border-slate-200/50 dark:border-slate-800/50 relative">
                        <div 
                          className={cn("h-full rounded-xl transition-all duration-1000 ease-out shadow-sm", 
                            scorecard.runway_months >= 18 ? "bg-gradient-to-r from-emerald-500 to-teal-400" : 
                            scorecard.runway_months >= 9 ? "bg-gradient-to-r from-amber-500 to-orange-400" : 
                            "bg-gradient-to-r from-rose-600 to-pink-500"
                          )}
                          style={{ width: `${Math.min(100, (scorecard.runway_months / 18) * 100)}%` }}
                        />
                     </div>
                     
                     <div className="grid grid-cols-2 gap-4 mt-10">
                        <div className="p-5 rounded-3xl bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800/50">
                           <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Inflow Focus</p>
                           <p className="text-xl font-black text-slate-900 dark:text-white font-outfit">{formatCompactNumber(scorecard.monthly_revenue)}/mo</p>
                        </div>
                        <div className="p-5 rounded-3xl bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800/50">
                           <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Target Zero</p>
                           <p className="text-xl font-black text-slate-900 dark:text-white font-outfit">
                             {new Date(Date.now() + scorecard.runway_months * 30 * 24 * 60 * 60 * 1000).toLocaleDateString("en-US", { month: "short", year: "numeric" })}
                           </p>
                        </div>
                     </div>
                  </div>
               </div>

               {/* Expense Intelligence */}
               <div className="glass-card rounded-[32px] p-8">
                  <h3 className="text-lg font-black text-slate-900 dark:text-white font-outfit tracking-tight mb-8">Capital Allocation</h3>
                  <div className="space-y-6">
                    {Object.entries(burnRate.breakdown_by_category)
                      .sort(([, a], [, b]) => (b as number) - (a as number))
                      .slice(0, 4)
                      .map(([category, amount], idx) => {
                        const colors = ["bg-indigo-500", "bg-purple-500", "bg-rose-500", "bg-amber-500"];
                        const percent = ((amount as number) / burnRate.monthly_burn) * 100;
                        return (
                          <div key={category} className="group cursor-default">
                             <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-3">
                                   <div className={cn("w-3 h-3 rounded-full shadow-lg transition-transform group-hover:scale-125", colors[idx] || "bg-slate-500")} />
                                   <span className="text-xs font-black text-slate-700 dark:text-slate-300 capitalize tracking-wide uppercase tracking-widest">{category}</span>
                                </div>
                                <span className="text-sm font-black text-slate-900 dark:text-white">{formatCurrency(amount as number)}</span>
                             </div>
                             <div className="h-2 bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden p-[2px] border border-slate-200/50 dark:border-slate-800/50">
                                <div 
                                  className={cn("h-full rounded-full transition-all duration-700 group-hover:opacity-80", colors[idx] || "bg-slate-500")}
                                  style={{ width: `${percent}%` }}
                                />
                             </div>
                          </div>
                        );
                      })}
                  </div>
                  <button className="w-full mt-8 py-3.5 text-[10px] font-black uppercase tracking-widest text-indigo-600 dark:text-indigo-400 bg-indigo-500/5 hover:bg-indigo-500/10 rounded-2xl transition-all border border-indigo-500/10">
                     View Complete Ledger
                  </button>
               </div>
            </div>
          </div>

          {/* Side Intelligence - 4 cols */}
          <div className="xl:col-span-4 space-y-8">
            
            {/* AI Strategic Insights */}
            <div className="bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-800 rounded-[40px] p-8 text-white relative overflow-hidden shadow-2xl shadow-indigo-500/20 group">
               <div className="absolute -right-8 -bottom-8 opacity-[0.15] rotate-12 transition-transform group-hover:rotate-45 duration-1000">
                  <Sparkles className="w-64 h-64" />
               </div>
               
               <div className="flex items-center gap-3 mb-8">
                  <div className="p-3 bg-white/20 rounded-2xl backdrop-blur-xl ring-1 ring-white/30">
                    <Zap className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-black font-outfit tracking-tight">AI Strategic Intel</h2>
                    <p className="text-[10px] font-black uppercase tracking-widest text-indigo-200 opacity-70">CFO Assistant Enabled</p>
                  </div>
               </div>
               
               <div className="space-y-5 relative z-10">
                  <div className="bg-white/10 backdrop-blur-md p-5 rounded-[24px] border border-white/10 hover:bg-white/20 transition-all cursor-default group/item">
                     <p className="text-[10px] font-black uppercase tracking-widest text-indigo-200 mb-2">Cloud Spend Optimization</p>
                     <p className="text-sm font-bold leading-relaxed group-hover/item:text-white">Recommend switching 3 EC2 instances to Reserved Instances for <span className="text-emerald-300 font-extrabold underline decoration-emerald-300/30">22% peak savings</span>.</p>
                  </div>
                  <div className="bg-white/10 backdrop-blur-md p-5 rounded-[24px] border border-white/10 hover:bg-white/20 transition-all cursor-default group/item">
                     <p className="text-[10px] font-black uppercase tracking-widest text-purple-200 mb-2">Talent Expansion Forecast</p>
                     <p className="text-sm font-bold leading-relaxed group-hover/item:text-white">Current MRR trajectory permits 2 additional H1 engineering hires without affecting the 18-month safety buffer.</p>
                  </div>
               </div>
               
               <button 
                  onClick={() => openChat("AI Strategic Insights")}
                  className="w-full mt-8 py-4 bg-white text-indigo-700 font-black text-xs uppercase tracking-widest rounded-2xl shadow-xl hover:shadow-2xl active:scale-[0.98] transition-all flex items-center justify-center gap-2 group/btn"
               >
                  Exploration Mode
                  <ChevronRight className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />
               </button>
            </div>

            {/* Critical Anomalies */}
            <div className="glass-card rounded-[32px] p-8 shadow-xl shadow-slate-200/50 dark:shadow-none">
               <div className="flex items-center justify-between mb-8">
                  <div>
                    <h3 className="text-lg font-black text-slate-900 dark:text-white font-outfit tracking-tight">Financial Anomalies</h3>
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Immediate Review Required</p>
                  </div>
                  <Link href="/anomalies" className="p-2 bg-slate-100 dark:bg-slate-800 rounded-xl hover:bg-indigo-500 hover:text-white transition-all">
                    <ChevronRight className="w-4 h-4" />
                  </Link>
               </div>
               
               <div className="space-y-4">
                  {alerts.alerts.slice(0, 3).map((alert: any) => (
                    <div key={alert.id} className="flex gap-4 p-5 rounded-[24px] border border-slate-100 dark:border-slate-800/50 hover:bg-white dark:hover:bg-slate-900/50 hover:shadow-lg transition-all group/card border-l-4" 
                      style={{ borderLeftColor: alert.severity === 'critical' ? '#ef4444' : '#f59e0b' }}
                    >
                       <div className={cn("p-3 h-fit rounded-2xl shrink-0 transition-transform group-hover/card:scale-110", alert.severity === "critical" ? "bg-rose-500/10 text-rose-500" : "bg-amber-500/10 text-amber-500")}>
                          <AlertTriangle className="w-5 h-5" />
                       </div>
                       <div className="min-w-0 flex-1">
                          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">{alert.severity}</p>
                          <p className="text-sm font-bold text-slate-900 dark:text-white truncate lg:whitespace-normal group-hover/card:text-indigo-600 transition-colors">{alert.description}</p>
                          <div className="flex items-center gap-3 mt-3">
                             <button onClick={() => openChat("Anomaly: " + alert.description)} className="text-[10px] font-black text-indigo-600 uppercase tracking-widest flex items-center gap-1">
                                Ask AI
                             </button>
                             <span className="w-1 h-1 rounded-full bg-slate-200" />
                             <span className="text-[10px] font-bold text-slate-400">{formatRelativeTime(alert.created_at)}</span>
                          </div>
                       </div>
                    </div>
                  ))}
               </div>
            </div>

            {/* Live Feed */}
            <div className="glass-card rounded-[32px] p-8">
               <div className="flex items-center justify-between mb-8">
                  <h3 className="text-lg font-black text-slate-900 dark:text-white font-outfit tracking-tight">Recent Activity</h3>
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
               </div>
               <div className="space-y-7">
                  {recentTransactions.map((tx) => (
                    <div key={tx.id} className="flex items-center gap-4 group cursor-default">
                       <div className={cn("w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 transition-all border border-transparent group-hover:border-current group-hover:scale-105", 
                          tx.amount > 0 ? "bg-emerald-500/10 text-emerald-600" : "bg-slate-100 dark:bg-slate-900 text-slate-500"
                       )}>
                          {tx.amount > 0 ? <ArrowUpRight className="w-5 h-5" /> : <ArrowDownRight className="w-5 h-5" />}
                       </div>
                       <div className="min-w-0 flex-1">
                          <p className="text-sm font-black text-slate-900 dark:text-white truncate tracking-tight group-hover:translate-x-1 transition-transform">{tx.name}</p>
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-0.5">{tx.date}</p>
                       </div>
                       <div className="text-right">
                          <p className={cn("text-base font-black font-outfit", tx.amount > 0 ? "text-emerald-500" : "text-slate-900 dark:text-white")}>
                             {tx.amount > 0 ? "+" : ""}{formatCompactNumber(tx.amount)}
                          </p>
                          <div className="flex justify-end gap-1 mt-1">
                             <div className="w-6 h-[3px] bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                <div className="w-full h-full bg-indigo-500 origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-700 delay-75" />
                             </div>
                          </div>
                       </div>
                    </div>
                  ))}
               </div>
               <button className="w-full mt-10 py-4 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-slate-900 dark:hover:text-white bg-slate-100/50 dark:bg-slate-900/50 rounded-2xl transition-all border border-slate-200/50 dark:border-slate-800/50">
                  Full Activity Log
               </button>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
