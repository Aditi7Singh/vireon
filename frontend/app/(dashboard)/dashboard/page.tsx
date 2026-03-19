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
   Globe,
   Hexagon,
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
   const runwayMonths = Number(scorecard.runway_months);
   const runwayLabel = Number.isFinite(runwayMonths) ? `${Math.round(runwayMonths)} MO` : "-";

   const handleConsultAI = () => {
      openChat("Financial Dashboard Analysis");
   };

   return (
      <div className="min-h-screen bg-slate-950 pb-20">
         <TopBar title="Financial Command Center" />

         <div className="p-8 space-y-10 max-w-[1600px] mx-auto">
            {/* Header Section */}
            <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8">
               <div className="space-y-4">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-bold uppercase tracking-wider">
                     <Clock className="w-3.5 h-3.5" />
                     Live Market Data Connected
                  </div>
                  <h1 className="text-4xl font-black text-white tracking-tight font-outfit uppercase">
                     Financial <span className="text-slate-500">Overview</span>
                  </h1>
                  <div className="flex items-center gap-4 text-slate-500 font-bold text-[10px] uppercase tracking-widest">
                     <div className="flex items-center gap-2">
                        <Globe className="w-3.5 h-3.5" />
                        <span>ERP Sync: ACTIVE</span>
                     </div>
                     <div className="w-1.5 h-1.5 rounded-full bg-slate-800" />
                     <div className="text-slate-400">Node ID: 0xFF-70A</div>
                  </div>
               </div>

               <div className="flex items-center gap-3">
                  <button className="btn-secondary text-xs">
                     <Download className="w-4 h-4" />
                     Export CSV
                  </button>
                  <button
                     onClick={handleConsultAI}
                     className="btn-primary text-xs flex items-center gap-2"
                  >
                     <Bot className="w-4 h-4" />
                     Run AI Audit
                  </button>
               </div>
            </div>

            {/* KPI Grid - Industrial Standard */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
               {[
                  { title: "Total Liquidity", value: formatCurrency(scorecard.total_cash), icon: DollarSign, trend: "+2.4%", trendColor: "text-emerald-500" },
                  { title: "Monthly Burn", value: formatCurrency(scorecard.monthly_gross_burn), icon: TrendingUp, trend: "-1.2%", trendColor: "text-emerald-500" },
                  { title: "Projected Runway", value: runwayLabel, icon: Calendar, trend: "Stable", trendColor: "text-slate-400" },
                  { title: "Core Revenue", value: formatCurrency(scorecard.monthly_revenue), icon: Target, trend: "+8.5%", trendColor: "text-emerald-500" },
               ].map((kpi, i) => (
                  <div key={i} className="bg-slate-900 border border-white/10 p-6 rounded-2xl shadow-lg group hover:border-indigo-500/30 transition-all">
                     <div className="flex items-center justify-between mb-4">
                        <div className="p-2 rounded-lg bg-white/5 text-slate-400 group-hover:text-indigo-400 transition-colors">
                           <kpi.icon className="w-5 h-5" />
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider ${kpi.trendColor}`}>{kpi.trend}</span>
                     </div>
                     <div className="space-y-1">
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{kpi.title}</span>
                        <div className="text-2xl font-black text-white font-outfit tracking-tight">{kpi.value}</div>
                     </div>
                  </div>
               ))}
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
               <div className="xl:col-span-8 space-y-8">
                  {/* Chart Area */}
                  <div className="bg-slate-900 border border-white/10 rounded-3xl p-8">
                     <div className="flex items-center justify-between mb-8">
                        <div>
                           <h2 className="text-xl font-bold text-white font-outfit uppercase tracking-tighter">
                              Cash Flow Intelligence
                           </h2>
                           <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-0.5">Revenue vs Expenditure Matrix</p>
                        </div>
                        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-white/5">
                           <button className="px-4 py-1.5 text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-white rounded-md">6 Months</button>
                           <button className="px-4 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 hover:text-white transition-all">Yearly</button>
                        </div>
                     </div>

                     <div className="h-[380px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                           <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                              <defs>
                                 <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.15} />
                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                 </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                              <XAxis
                                 dataKey="date"
                                 axisLine={false}
                                 tickLine={false}
                                 tick={{ fill: '#64748b', fontSize: 11, fontWeight: 700 }}
                              />
                              <YAxis
                                 axisLine={false}
                                 tickLine={false}
                                 tick={{ fill: '#64748b', fontSize: 11, fontWeight: 700 }}
                                 tickFormatter={(value) => `$${value / 1000}K`}
                              />
                              <Tooltip
                                 contentStyle={{
                                    backgroundColor: '#0f172a',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    borderRadius: '12px',
                                    fontSize: '11px',
                                    fontWeight: '700'
                                 }}
                              />
                              <Area
                                 type="monotone"
                                 dataKey="Revenue"
                                 stroke="#6366f1"
                                 strokeWidth={3}
                                 fillOpacity={1}
                                 fill="url(#colorRevenue)"
                                 animationDuration={1500}
                              />
                              <Area
                                 type="monotone"
                                 dataKey="Expenses"
                                 stroke="#94a3b8"
                                 strokeWidth={2}
                                 strokeDasharray="4 4"
                                 fill="transparent"
                              />
                           </AreaChart>
                        </ResponsiveContainer>
                     </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                     {/* Resource Velocity */}
                     <div className="bg-slate-900 border border-white/10 rounded-2xl p-8 border-l-4 border-l-indigo-600">
                        <h3 className="text-lg font-bold text-white font-outfit uppercase tracking-tight mb-6">Runway Sustainability</h3>
                        <div className="space-y-6">
                           <div className="flex justify-between items-end">
                              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Safety Margin</span>
                              <span className="text-2xl font-black text-white font-outfit tracking-tight">{runwayLabel}</span>
                           </div>
                           <div className="h-2 bg-slate-950 rounded-full overflow-hidden border border-white/5">
                              <div
                                 className="h-full bg-indigo-500 transition-all duration-1000"
                                 style={{ width: `${Math.min(100, (scorecard.runway_months / 24) * 100)}%` }}
                              />
                           </div>
                           <div className="grid grid-cols-2 gap-4 pt-2">
                              <div className="bg-slate-950 p-4 rounded-xl border border-white/5">
                                 <p className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.15em] mb-1">Target</p>
                                 <p className="text-base font-bold text-white">18.0 MO</p>
                              </div>
                              <div className="bg-slate-950 p-4 rounded-xl border border-white/5">
                                 <p className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.15em] mb-1">Status</p>
                                 <p className="text-base font-bold text-emerald-500 uppercase">Secure</p>
                              </div>
                           </div>
                        </div>
                     </div>

                     {/* Allocation Logic */}
                     <div className="bg-slate-900 border border-white/10 rounded-2xl p-8">
                        <h3 className="text-lg font-bold text-white font-outfit uppercase tracking-tight mb-6">Capital Allocation</h3>
                        <div className="space-y-5">
                           {Object.entries(burnRate.breakdown_by_category).slice(0, 3).map(([cat, val]) => (
                              <div key={cat} className="space-y-2">
                                 <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-widest">
                                    <span className="text-slate-500">{cat}</span>
                                    <span className="text-white">{formatCurrency(val as number)}</span>
                                 </div>
                                 <div className="h-1.5 bg-slate-950 rounded-full overflow-hidden">
                                    <div className="h-full bg-slate-700 w-[60%]" style={{ width: `${Math.min(100, (val as number / burnRate.monthly_burn) * 100)}%` }} />
                                 </div>
                              </div>
                           ))}
                        </div>
                     </div>
                  </div>
               </div>

               <div className="xl:col-span-4 space-y-8">
                  {/* Executive Action */}
                  <div className="bg-indigo-600 rounded-3xl p-8 text-white relative shadow-xl overflow-hidden group">
                     <Hexagon className="absolute -right-8 -bottom-8 w-40 h-40 opacity-10 rotate-12" />
                     <h3 className="text-xl font-black font-outfit uppercase tracking-tight mb-4">Vireon Intelligence</h3>
                     <p className="text-sm font-medium text-indigo-100/90 leading-relaxed mb-8">
                        Operational efficiency protocols identified. Optimization can reclaim 12% of infrastructure overhead.
                     </p>
                     <button
                        onClick={() => openChat("Optimize infrastructure")}
                        className="w-full py-4 bg-white text-indigo-700 text-[10px] font-black uppercase tracking-[0.2em] rounded-xl hover:bg-slate-100 transition-all flex items-center justify-center gap-2"
                     >
                        <Zap className="w-4 h-4" />
                        Review Recommendations
                     </button>
                  </div>

                  {/* Recent Transactions */}
                  <div className="bg-slate-900 border border-white/10 rounded-3xl p-8">
                     <div className="flex items-center justify-between mb-8">
                        <h3 className="text-lg font-bold text-white font-outfit uppercase tracking-tight">Ledger Feed</h3>
                        <div className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest bg-emerald-500/10 px-2 py-0.5 rounded">Real-time</div>
                     </div>
                     <div className="space-y-6">
                        {recentTransactions.map(tx => (
                           <div key={tx.id} className="flex items-center gap-4 group cursor-pointer">
                              <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border border-white/5 transition-all ${tx.amount > 0 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-slate-800 text-slate-500'}`}>
                                 {tx.amount > 0 ? <ArrowUpRight className="w-5 h-5" /> : <TrendingUp className="w-5 h-5 rotate-180" />}
                              </div>
                              <div className="flex-1 min-w-0">
                                 <p className="text-[11px] font-bold text-white uppercase tracking-wider truncate">{tx.name}</p>
                                 <p className="text-[9px] font-medium text-slate-600 uppercase tracking-widest mt-0.5">{tx.date}</p>
                              </div>
                              <span className={`text-xs font-bold ${tx.amount > 0 ? 'text-emerald-500' : 'text-slate-400'}`}>
                                 {tx.amount > 0 ? '+' : ''}{formatCompactNumber(tx.amount)}
                              </span>
                           </div>
                        ))}
                     </div>
                  </div>
               </div>
            </div>
         </div>
      </div>
   );
}

