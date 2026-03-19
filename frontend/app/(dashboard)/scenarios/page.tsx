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
      <div className="min-h-screen bg-slate-950 pb-20">
         <TopBar title="Strategic Simulations" />

         <div className="p-8 space-y-10 max-w-[1600px] mx-auto">
            {/* Header Section */}
            <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8">
               <div className="space-y-4">
                  <h1 className="text-4xl font-bold text-white tracking-tight">
                     Scenario <span className="text-slate-400">Analysis</span>
                  </h1>
                  <div className="flex items-center gap-4 text-slate-500 font-medium text-xs">
                     <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-indigo-500" />
                        <span>Impact Assessment Protocol</span>
                     </div>
                     <div className="w-1 h-1 rounded-full bg-slate-700" />
                     <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-emerald-500" />
                        <span>Sim Engine: Ready</span>
                     </div>
                  </div>
               </div>

               <button
                  onClick={() => openChat("Advanced Predictive Modeling Request")}
                  className="btn-primary"
               >
                  <Sparkles className="w-4 h-4" />
                  New Simulation
               </button>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-10">
               {/* Hiring Simulation */}
               <SimulationCard
                  title="Expansion Modeling"
                  subtitle="Simulate headcount & overhead growth"
                  icon={Briefcase}
                  color="indigo"
               >
                  <div className="space-y-8">
                     <div className="space-y-3">
                        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Headcount Addition</label>
                        <div className="flex items-center gap-6 bg-slate-900 p-4 rounded-xl border border-slate-800">
                           <input
                              type="range" min="1" max="50" step="1"
                              value={hiringSim.count}
                              onChange={(e) => setHiringSim({ ...hiringSim, count: parseInt(e.target.value) })}
                              className="flex-grow accent-indigo-500 h-1 bg-slate-800 rounded-full appearance-none cursor-pointer"
                           />
                           <span className="w-12 text-center text-xl font-bold text-white tracking-tight">{hiringSim.count}</span>
                        </div>
                     </div>

                     <div className="space-y-3">
                        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Average Salary ($k)</label>
                        <div className="flex items-center gap-6 bg-slate-900 p-4 rounded-xl border border-slate-800">
                           <input
                              type="range" min="50" max="500" step="10"
                              value={hiringSim.salary / 1000}
                              onChange={(e) => setHiringSim({ ...hiringSim, salary: parseInt(e.target.value) * 1000 })}
                              className="flex-grow accent-indigo-500 h-1 bg-slate-800 rounded-full appearance-none cursor-pointer"
                           />
                           <span className="w-12 text-center text-xl font-bold text-white tracking-tight">{hiringSim.salary / 1000}k</span>
                        </div>
                     </div>

                     <div className="pt-8 border-t border-slate-800 flex items-center justify-between">
                        <div>
                           <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Runway Impact</p>
                           <p className="text-3xl font-bold text-rose-500 tracking-tighter uppercase">-{(hiringSim.count * 0.4).toFixed(1)} Months</p>
                        </div>
                        <button className="btn-primary">
                           Inject Scenario
                        </button>
                     </div>
                  </div>
               </SimulationCard>

               {/* Revenue Stress Test */}
               <SimulationCard
                  title="Market Volatility"
                  subtitle="Stress test capital velocity"
                  icon={Globe}
                  color="emerald"
               >
                  <div className="space-y-8">
                     <div className="grid grid-cols-2 gap-4">
                        <StressBox label="Aggressive" value="+25%" desc="Optimization case" active />
                        <StressBox label="Baseline" value="+12%" desc="Strategic target" />
                        <StressBox label="Volatility" value="-15%" desc="Bear case buffer" />
                        <StressBox label="Critical" value="-40%" desc="Crisis protocol" color="rose" />
                     </div>

                     <div className="pt-8 border-t border-slate-800 flex items-center justify-between">
                        <div>
                           <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Potential Extension</p>
                           <p className="text-3xl font-bold text-emerald-500 tracking-tighter uppercase">+5.8 Months</p>
                        </div>
                        <button className="btn-secondary">
                           Generate Audit
                        </button>
                     </div>
                  </div>
               </SimulationCard>

               {/* Scenario Comparison Table */}
               <div className="xl:col-span-2 glass-card rounded-[48px] overflow-hidden border-white/5 shadow-2xl">
                  <div className="p-10 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                     <div>
                        <h3 className="text-2xl font-black text-white font-outfit tracking-tighter uppercase">Stored Strategy Nodes</h3>
                        <p className="text-[9px] text-slate-600 font-black uppercase tracking-[0.2em] mt-2">Historical version control for strategic maneuvers</p>
                     </div>
                     <button className="flex items-center gap-3 px-6 py-3 bg-white/5 border border-white/5 text-white rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] hover:bg-white/10 transition-all">
                        <Plus className="w-4 h-4 text-indigo-500" /> Save Matrix
                     </button>
                  </div>

                  {/* Scenario Comparison Table */}
                  <div className="glass-card rounded-2xl overflow-hidden border-slate-800">
                     <div className="p-8 border-b border-slate-800">
                        <h3 className="text-xl font-bold text-white tracking-tight">Active Simulations</h3>
                     </div>
                     <div className="overflow-x-auto">
                        <table className="w-full text-left">
                           <thead>
                              <tr className="bg-slate-900/50">
                                 <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-wider text-slate-500">Scenario</th>
                                 <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-wider text-slate-500">Burn Rate</th>
                                 <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-wider text-slate-500">Runway</th>
                                 <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-wider text-slate-500">Risk Profile</th>
                                 <th className="px-8 py-4"></th>
                              </tr>
                           </thead>
                           <tbody className="divide-y divide-slate-800">
                              <ScenarioRow name="Conservative Reserve" burn="$340k" runway="14 MO" stability="Healthy" status="success" />
                              <ScenarioRow name="Expansion Strategy" burn="$720k" runway="6 MO" stability="Critical" status="danger" />
                              <ScenarioRow name="Product Pivot" burn="$410k" runway="11 MO" stability="Moderate" status="warning" />
                           </tbody>
                        </table>
                     </div>
                  </div>
               </div>
            </div>
         </div>
      </div>
   );
}

function SimulationCard({ title, subtitle, icon: Icon, color, children }: any) {
   return (
      <div className="glass-card rounded-2xl p-8 border-slate-800">
         <div className="flex items-start gap-4 mb-8">
            <div className={cn(
               "p-3 rounded-xl border",
               color === 'indigo' ? "bg-indigo-500/10 border-indigo-500/20 text-indigo-500" : "bg-emerald-500/10 border-emerald-500/20 text-emerald-500"
            )}>
               <Icon className="w-6 h-6" />
            </div>
            <div className="space-y-1">
               <h2 className="text-2xl font-bold text-white tracking-tight">{title}</h2>
               <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{subtitle}</p>
            </div>
         </div>
         {children}
      </div>
   );
}

function StressBox({ label, value, desc, active, color = "indigo" }: any) {
   return (
      <div className={cn(
         "p-5 rounded-xl border transition-all cursor-pointer",
         active
            ? (color === 'indigo' ? "bg-indigo-600/10 border-indigo-500/50 shadow-lg" : "bg-rose-600/10 border-rose-500/50 shadow-lg")
            : "bg-slate-900 border-slate-800 hover:border-slate-700"
      )}>
         <p className="text-[8px] font-bold uppercase tracking-wider text-slate-500 mb-1">{label}</p>
         <p className={cn(
            "text-xl font-bold tracking-tight",
            active ? (color === "indigo" ? "text-indigo-400" : "text-rose-400") : "text-white"
         )}>{value}</p>
         <p className="text-[10px] font-medium text-slate-600 mt-1 uppercase tracking-wider">{desc}</p>
      </div>
   );
}

function ScenarioRow({ name, burn, runway, stability, status }: any) {
   return (
      <tr className="group hover:bg-slate-900/50 transition-all border-none">
         <td className="px-8 py-6">
            <span className="text-sm font-bold text-white tracking-tight">{name}</span>
         </td>
         <td className="px-8 py-6">
            <span className="text-sm font-medium text-slate-400">{burn}</span>
         </td>
         <td className="px-8 py-6">
            <span className="text-base font-bold text-white">{runway}</span>
         </td>
         <td className="px-8 py-6">
            <span className={cn(
               "px-3 py-1 rounded text-[10px] font-bold uppercase tracking-wider border",
               status === 'success' ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/10" :
                  status === 'danger' ? "bg-rose-500/10 text-rose-500 border-rose-500/10" :
                     "bg-amber-500/10 text-amber-500 border-amber-500/10"
            )}>
               {stability}
            </span>
         </td>
         <td className="px-8 py-6 text-right">
            <button className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-500 hover:text-white hover:bg-indigo-600 transition-all">
               <ArrowRight className="w-4 h-4" />
            </button>
         </td>
      </tr>
   );
}
