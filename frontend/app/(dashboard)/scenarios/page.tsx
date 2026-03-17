"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { formatCurrency, cn } from "@/lib/utils";
import { 
  Users, 
  TrendingUp, 
  Trash2, 
  Zap, 
  ArrowRight, 
  Sparkles, 
  Target, 
  Shield, 
  AlertCircle,
  Clock,
  Briefcase,
  Globe,
  Plus,
} from "lucide-react";
import { useAppStore } from "@/lib/store";

export default function ScenariosPage() {
    const { openChat } = useAppStore();
    const [hiringSim, setHiringSim] = useState({ count: 1, salary: 100000 });
    const [revSim, setRevSim] = useState({ percentage: 10 });

    return (
        <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950/50 pb-12">
            <TopBar title="War Room: Simulations" />

            <div className="p-8 space-y-8 max-w-[1400px] mx-auto">
                {/* Header */}
                <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
                  <div className="space-y-1">
                    <h1 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight font-outfit">
                       Simulations
                    </h1>
                    <div className="flex items-center gap-2 text-slate-500 font-medium text-sm">
                       <Target className="w-4 h-4 text-indigo-500" />
                       <span>Predictive modeling of capital maneuvers</span>
                       <span className="w-1 h-1 rounded-full bg-slate-300" />
                       <span className="text-indigo-500 font-bold">Real-time Impact</span>
                    </div>
                  </div>
                  
                  <button 
                     onClick={() => openChat("Predictive Modeling")}
                     className="flex items-center gap-2 px-6 py-3 text-sm font-bold text-white bg-indigo-600 rounded-2xl hover:bg-indigo-500 transition-all shadow-xl shadow-indigo-500/25 active:scale-95 group"
                  >
                     <Zap className="w-4 h-4" />
                     Forecast with AI
                  </button>
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                    {/* Hiring Simulation */}
                    <SimulationCard 
                      title="Expansion Modeling" 
                      subtitle="Simulate team growth and overhead impact"
                      icon={Briefcase}
                      color="indigo"
                    >
                        <div className="space-y-6">
                            <div className="space-y-3">
                                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Headcount Addition</label>
                                <div className="flex items-center gap-4">
                                   <input 
                                      type="range" min="1" max="20" step="1"
                                      value={hiringSim.count}
                                      onChange={(e) => setHiringSim({...hiringSim, count: parseInt(e.target.value)})}
                                      className="flex-grow accent-indigo-600"
                                   />
                                   <span className="w-12 text-center text-sm font-black text-slate-900 dark:text-white">{hiringSim.count}</span>
                                </div>
                            </div>

                            <div className="space-y-3">
                                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Avg. Annual Comp ($k)</label>
                                <div className="flex items-center gap-4">
                                   <input 
                                      type="range" min="50" max="300" step="10"
                                      value={hiringSim.salary / 1000}
                                      onChange={(e) => setHiringSim({...hiringSim, salary: parseInt(e.target.value) * 1000})}
                                      className="flex-grow accent-indigo-600"
                                   />
                                   <span className="w-12 text-center text-sm font-black text-slate-900 dark:text-white">{hiringSim.salary / 1000}k</span>
                                </div>
                            </div>

                            <div className="pt-6 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                               <div>
                                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Runway impact</p>
                                  <p className="text-2xl font-black text-rose-500 font-outfit">-{(hiringSim.count * 0.4).toFixed(1)} Months</p>
                               </div>
                               <button className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-500/20 active:scale-[0.98]">
                                  Apply Scenario
                               </button>
                            </div>
                        </div>
                    </SimulationCard>

                    {/* Revenue Stress Test */}
                    <SimulationCard 
                      title="Revenue Stress Test" 
                      subtitle="Model volatility in churn or conversion"
                      icon={Globe}
                      color="emerald"
                    >
                        <div className="space-y-8">
                            <div className="grid grid-cols-2 gap-4">
                               <StressBox label="Growth" value="+15%" desc="Bull Case" active />
                               <StressBox label="Standard" value="+5%" desc="Target" />
                               <StressBox label="Downturn" value="-10%" desc="Bear Case" />
                               <StressBox label="Crisis" value="-30%" desc="Critical" color="rose" />
                            </div>

                            <div className="pt-6 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                               <div>
                                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Runway extension</p>
                                  <p className="text-2xl font-black text-emerald-500 font-outfit">+4.2 Months</p>
                               </div>
                               <button className="px-5 py-2.5 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-xl text-xs font-black uppercase tracking-widest hover:bg-slate-200 dark:hover:bg-slate-700 transition-all active:scale-[0.98]">
                                  Export Report
                               </button>
                            </div>
                        </div>
                    </SimulationCard>

                    {/* Scenario Comparison Table */}
                    <div className="xl:col-span-2 glass-card rounded-[32px] overflow-hidden border border-slate-200 dark:border-slate-800/50">
                        <div className="p-8 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                           <div>
                              <h3 className="text-xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">Saved Scenarios</h3>
                              <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">Version control for your strategy</p>
                           </div>
                           <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600/10 text-indigo-600 rounded-xl text-xs font-black uppercase tracking-widest hover:bg-indigo-600/20 transition-all">
                              <Plus className="w-4 h-4" /> Save current
                           </button>
                        </div>
                        
                        <div className="overflow-x-auto">
                           <table className="w-full text-left">
                              <thead>
                                 <tr className="bg-slate-50/50 dark:bg-slate-900/50">
                                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-slate-400">Scenario Name</th>
                                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-slate-400">Total Burn</th>
                                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-slate-400">Runway</th>
                                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-slate-400">Stability</th>
                                    <th className="px-8 py-5"></th>
                                 </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                 <ScenarioRow name="Conservative Freeze" burn="$340k" runway="14 mo" stability="High" status="success" />
                                 <ScenarioRow name="Series B Prep" burn="$520k" runway="8 mo" stability="Low" status="danger" />
                                 <ScenarioRow name="Product Launch V2" burn="$410k" runway="11 mo" stability="Medium" status="warning" />
                              </tbody>
                           </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function SimulationCard({ title, subtitle, icon: Icon, color, children }: any) {
  const colorMap: any = {
     indigo: "bg-indigo-500/10 text-indigo-600 border-indigo-500/20",
     emerald: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  };

  return (
    <div className="glass-card rounded-[40px] p-10 border border-slate-200 dark:border-slate-800/50 hover:border-indigo-500/20 transition-all shadow-sm">
       <div className="flex items-start gap-4 mb-10">
          <div className={cn("p-4 rounded-2xl", colorMap[color])}>
             <Icon className="w-6 h-6" />
          </div>
          <div>
             <h2 className="text-2xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">{title}</h2>
             <p className="text-sm text-slate-500 font-medium">{subtitle}</p>
          </div>
       </div>
       {children}
    </div>
  );
}

function StressBox({ label, value, desc, active, color = "indigo" }: any) {
  const colors: any = {
    indigo: {
       active: "border-indigo-500 bg-indigo-500/5 ring-4 ring-indigo-500/5",
       inactive: "border-slate-200 hover:border-indigo-300 dark:border-slate-800"
    },
    rose: {
       active: "border-rose-500 bg-rose-500/5 ring-4 ring-rose-500/5",
       inactive: "border-slate-200 hover:border-rose-300 dark:border-slate-800"
    }
  };

  return (
    <div className={cn(
       "p-4 rounded-2xl border transition-all cursor-pointer group",
       active ? colors[color].active : colors[color].inactive
    )}>
       <p className="text-[8px] font-black uppercase tracking-widest text-slate-400 group-hover:text-slate-600 transition-colors">{label}</p>
       <p className={cn("text-xl font-black font-outfit mt-1", active ? (color === "indigo" ? "text-indigo-600" : "text-rose-600") : "text-slate-900 dark:text-white")}>{value}</p>
       <p className="text-[10px] font-bold text-slate-500 mt-1">{desc}</p>
    </div>
  );
}

function ScenarioRow({ name, burn, runway, stability, status }: any) {
   const statusColors: any = {
      success: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
      danger: "bg-rose-500/10 text-rose-500 border-rose-500/20",
      warning: "bg-amber-500/10 text-amber-500 border-amber-500/20",
   };

   return (
      <tr className="group hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-colors">
         <td className="px-8 py-5">
            <span className="text-sm font-black text-slate-900 dark:text-white tracking-tight">{name}</span>
         </td>
         <td className="px-8 py-5">
            <span className="text-sm font-bold text-slate-500">{burn}</span>
         </td>
         <td className="px-8 py-5">
            <span className="text-sm font-black text-slate-900 dark:text-white font-outfit">{runway}</span>
         </td>
         <td className="px-8 py-5">
            <span className={cn("px-2.5 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest border", statusColors[status])}>
               {stability}
            </span>
         </td>
         <td className="px-8 py-5 text-right">
            <button className="p-2 text-slate-400 hover:text-indigo-600 transition-colors">
               <ArrowRight className="w-4 h-4" />
            </button>
         </td>
      </tr>
   );
}
