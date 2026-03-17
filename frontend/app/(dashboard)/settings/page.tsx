"use client";

import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import {
  Settings,
  User,
  Building2,
  Bell,
  Shield,
  Key,
  Link2,
  Palette,
  Globe,
  Database,
  RefreshCw,
  Sparkles,
  Save,
  Check,
  ChevronRight,
  Monitor,
  Cloud,
  Zap,
} from "lucide-react";
import { useState } from "react";

export default function SettingsPage() {
  const { isSyncing, setIsSyncing } = useAppStore();
  const [activeTab, setActiveTab] = useState("company");
  const [saved, setSaved] = useState(false);

  const tabs = [
    { id: "company", label: "Entity Configuration", icon: Building2, desc: "Organization details & structural data" },
    { id: "profile", label: "Executive Profile", icon: User, desc: "Personal identity & access scope" },
    { id: "notifications", label: "Intelligence Alerts", icon: Bell, desc: "Thresholds for anomaly detection" },
    { id: "security", label: "Cyber Security", icon: Shield, desc: "Enforce protocol and data protection" },
    { id: "rbac", label: "Team & Protocol", icon: Shield, desc: "Manage role-based access & permissions" },
    { id: "integrations", label: "Data Pipeline", icon: Link2, desc: "Sync with external financial sources" },
    { id: "api", label: "Neural Access", icon: Zap, desc: "LLM endpoints & vector configurations" },
  ];

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950/50 pb-12">
      <TopBar title="System Configuration" />

      <div className="p-8 max-w-[1400px] mx-auto">
        <div className="flex flex-col lg:flex-row gap-12">
          
          {/* Enhanced Navigation */}
          <div className="lg:w-80 shrink-0 space-y-8">
            <div>
               <h1 className="text-3xl font-black text-slate-900 dark:text-white font-outfit tracking-tight mb-2">Control Center</h1>
               <p className="text-xs font-black text-slate-400 uppercase tracking-widest">Global platform parameters</p>
            </div>

            <nav className="space-y-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "w-full group flex items-start gap-4 p-4 rounded-3xl transition-all text-left border relative overflow-hidden",
                    activeTab === tab.id
                      ? "bg-white dark:bg-slate-900 border-indigo-500/20 shadow-xl shadow-indigo-500/5"
                      : "border-transparent text-slate-500 hover:bg-white/50 dark:hover:bg-slate-900/50 hover:border-slate-200 dark:hover:border-slate-800"
                  )}
                >
                  {activeTab === tab.id && <div className="absolute left-0 top-4 bottom-4 w-1 bg-indigo-600 rounded-full" />}
                  <div className={cn(
                    "p-2.5 rounded-xl transition-colors group-hover:scale-110",
                    activeTab === tab.id ? "bg-indigo-600 text-white" : "bg-slate-100 dark:bg-slate-800 group-hover:bg-indigo-500/10"
                  )}>
                    <tab.icon className="w-5 h-5" />
                  </div>
                  <div className="flex-grow min-w-0">
                    <p className={cn(
                      "text-sm font-black tracking-tight",
                      activeTab === tab.id ? "text-slate-900 dark:text-white" : "text-slate-600 dark:text-slate-400"
                    )}>{tab.label}</p>
                    <p className="text-[10px] font-medium text-slate-400 truncate mt-0.5">{tab.desc}</p>
                  </div>
                </button>
              ))}
            </nav>
          </div>

          {/* Form Area */}
          <div className="flex-1 space-y-8">
            {activeTab === "company" && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="glass-card rounded-[40px] p-10 border border-slate-200 dark:border-slate-800/50">
                   <div className="flex items-center justify-between mb-10">
                      <div>
                         <h2 className="text-2xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">Entity Information</h2>
                         <p className="text-xs font-black text-slate-400 uppercase tracking-widest mt-1">Core architectural data</p>
                      </div>
                      <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center text-indigo-600">
                         <Building2 className="w-6 h-6" />
                      </div>
                   </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <Field label="Organization Identity" placeholder="Acme Global Inc" defaultValue="Acme Corp" />
                    <Field label="Operational Domain" type="select" options={['Technology', 'Finance', 'Logistics', 'Energy']} />
                    <Field label="Labor Force Magnitude" type="select" options={['1-20', '21-100', '101-500', '500+']} />
                    <Field label="Fiscal Alignment" type="select" options={['Jan-Dec', 'Apr-Mar', 'Jul-Jun']} />
                  </div>
                </div>

                <div className="glass-card rounded-[40px] p-10 border border-slate-200 dark:border-slate-800/50">
                  <h2 className="text-xl font-black text-slate-900 dark:text-white font-outfit tracking-tight mb-8">Localization Protocols</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <Field label="Settlement Currency" type="select" options={['USD ($)', 'EUR (€)', 'GBP (£)', 'INR (₹)']} />
                    <Field label="Temporal Zone" type="select" options={['UTC-5 (EST)', 'UTC-8 (PST)', 'UTC+0 (GMT)', 'UTC+5:30 (IST)']} />
                  </div>
                </div>

                <div className="flex items-center justify-end">
                   <SaveButton saved={saved} onClick={handleSave} />
                </div>
              </div>
            )}

            {activeTab === "integrations" && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="glass-card rounded-[40px] p-10 border border-slate-200 dark:border-slate-800/50">
                   <div className="flex items-center justify-between mb-10">
                      <div>
                         <h2 className="text-2xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">Active Pipelines</h2>
                         <p className="text-xs font-black text-slate-400 uppercase tracking-widest mt-1">Real-time data synchronization</p>
                      </div>
                      <RefreshCw className={cn("w-5 h-5 text-slate-400", isSyncing && "animate-spin")} />
                   </div>
                  
                  <div className="space-y-4">
                    {[
                      { name: "QuickBooks Prime", status: "Operational", icon: "📘", color: "text-blue-500" },
                      { name: "Stripe Connect", status: "Operational", icon: "💳", color: "text-indigo-500" },
                      { name: "Plaid Nexus", status: "Operational", icon: "🏦", color: "text-emerald-500" },
                      { name: "Sage Intacct", status: "Terminated", icon: "💎", color: "text-slate-400" },
                    ].map((integration) => (
                      <div
                        key={integration.name}
                        className="flex items-center justify-between p-6 bg-slate-50 dark:bg-slate-900/50 rounded-3xl border border-slate-100 dark:border-slate-800/50 group"
                      >
                        <div className="flex items-center gap-5">
                          <div className="w-12 h-12 bg-white dark:bg-slate-800 rounded-2xl flex items-center justify-center text-2xl shadow-sm group-hover:scale-110 transition-transform">
                             {integration.icon}
                          </div>
                          <div>
                            <p className="font-black text-slate-900 dark:text-white tracking-tight">
                              {integration.name}
                            </p>
                            <p className={cn(
                              "text-[10px] font-black uppercase tracking-widest mt-0.5",
                              integration.status === "Operational" ? "text-emerald-500" : "text-slate-500"
                            )}>
                              System {integration.status}
                            </p>
                          </div>
                        </div>
                        <button className="px-5 py-2 text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800 rounded-xl hover:bg-white dark:hover:bg-slate-800 transition-all">
                          {integration.status === "Operational" ? "Configure" : "Initialize"}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass-card rounded-[40px] p-10 border border-slate-200 dark:border-slate-800/50">
                   <h3 className="text-xl font-black text-slate-900 dark:text-white font-outfit tracking-tight mb-8">Available Nodes</h3>
                   <div className="grid grid-cols-2 sm:grid-cols-3 gap-6">
                     {["Netsuite", "Xero", "Gusto", "Ramp", "Brex", "Bill.com"].map((name) => (
                       <button
                         key={name}
                         className="flex flex-col items-center justify-center gap-4 p-8 bg-white dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800 rounded-[32px] hover:border-indigo-500/30 hover:shadow-xl hover:shadow-indigo-500/5 transition-all group"
                       >
                         <div className="w-12 h-12 bg-slate-50 dark:bg-slate-800 rounded-2xl flex items-center justify-center grayscale group-hover:grayscale-0 group-hover:scale-110 transition-all">
                            <Cloud className="w-6 h-6 text-slate-400 group-hover:text-indigo-600" />
                         </div>
                         <span className="text-xs font-black uppercase tracking-widest text-slate-600 dark:text-slate-300">{name}</span>
                       </button>
                     ))}
                   </div>
                </div>
              </div>
            )}

            {activeTab === "rbac" && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="glass-card rounded-[40px] p-10 border border-slate-200 dark:border-slate-800/50">
                  <div className="flex items-center justify-between mb-10">
                    <div>
                      <h2 className="text-2xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">Team & Protocol</h2>
                      <p className="text-xs font-black text-slate-400 uppercase tracking-widest mt-1">Identity & access management</p>
                    </div>
                    <button className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-indigo-500 shadow-lg shadow-indigo-600/20 transition-all">
                       <User className="w-3.5 h-3.5" />
                       Invite Member
                    </button>
                  </div>

                  <div className="space-y-4">
                    {[
                      { name: "Aditi Singh", role: "Super Admin", email: "aditi@vireon.ai", avatar: "AS" },
                      { name: "Saurabh Garg", role: "Financial Moderator", email: "saurabh@vireon.ai", avatar: "SG" },
                      { name: "Manoj Kumar", role: "Data Analyst", email: "manoj@vireon.ai", avatar: "MK" },
                    ].map((member) => (
                      <div key={member.email} className="flex items-center justify-between p-6 bg-slate-50 dark:bg-slate-900/50 rounded-3xl border border-slate-100 dark:border-slate-800/50">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center text-indigo-600 font-bold">
                            {member.avatar}
                          </div>
                          <div>
                            <p className="font-bold text-slate-900 dark:text-white">{member.name}</p>
                            <p className="text-xs text-slate-500">{member.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-6">
                           <span className="text-[10px] font-black uppercase tracking-widest text-indigo-500 bg-indigo-500/10 px-3 py-1.5 rounded-xl">
                              {member.role}
                           </span>
                           <button className="p-2 text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors">
                              <ChevronRight className="w-5 h-5" />
                           </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass-card rounded-[40px] p-10 border border-slate-200 dark:border-slate-800/50">
                   <h3 className="text-xl font-black text-slate-900 dark:text-white font-outfit tracking-tight mb-8">Access Protocols</h3>
                   <div className="space-y-6">
                      <div className="flex items-center justify-between">
                         <div>
                            <p className="font-bold text-slate-900 dark:text-white">Multi-Factor Authentication</p>
                            <p className="text-xs text-slate-500">Enforce 2FA for all Super Admin accounts</p>
                         </div>
                         <div className="w-12 h-6 bg-indigo-600 rounded-full relative">
                            <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm" />
                         </div>
                      </div>
                      <div className="flex items-center justify-between">
                         <div>
                            <p className="font-bold text-slate-900 dark:text-white">Neural Isolation</p>
                            <p className="text-xs text-slate-500">Prevent AI from accessing Payroll PII data</p>
                         </div>
                         <div className="w-12 h-6 bg-indigo-600 rounded-full relative">
                            <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm" />
                         </div>
                      </div>
                   </div>
                </div>
              </div>
            )}

            {activeTab === "api" && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                 <div className="glass-card rounded-[40px] p-10 border border-slate-200 dark:border-slate-800/50">
                    <div className="flex items-center gap-3 mb-10">
                       <Zap className="w-6 h-6 text-amber-500" />
                       <h2 className="text-2xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">Neural Configuration</h2>
                    </div>
                    
                    <div className="space-y-8">
                       <Field label="Groq AI Token" type="password" defaultValue="gsk_neural_8b2c_locked" />
                       <Field label="OpenRouter Gateway" type="password" defaultValue="sk-or-v1-neural-gate" />
                       <Field label="Local Vector Cluster" placeholder="http://localhost:11434" defaultValue="http://localhost:11434" />
                    </div>
                 </div>

                 <div className="flex items-center justify-end">
                    <SaveButton saved={saved} onClick={handleSave} label="Authorize neural keys" />
                 </div>
              </div>
            )}

            {activeTab !== "company" && activeTab !== "integrations" && activeTab !== "api" && activeTab !== "rbac" && (
              <div className="glass-card rounded-[40px] p-20 text-center border border-slate-200 dark:border-slate-800/50">
                <Settings className="w-16 h-16 text-slate-200 dark:text-slate-800 mx-auto mb-6 animate-pulse" />
                <h3 className="text-2xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">
                  Configuration Pending
                </h3>
                <p className="text-slate-500 font-medium max-w-xs mx-auto mt-2">
                  This architectural module is currently being finalized for high-availability.
                </p>
                <button 
                   onClick={() => setActiveTab('company')}
                   className="mt-8 text-xs font-black uppercase tracking-widest text-indigo-600 hover:text-indigo-500 transition-colors"
                >
                   Return to Entity Config
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, type = "text", placeholder, defaultValue, options }: any) {
  return (
    <div className="space-y-2">
      <label className="block text-[10px] font-black uppercase tracking-widest text-slate-400">
        {label}
      </label>
      {type === "select" ? (
         <select className="w-full h-14 px-6 border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 text-sm font-bold text-slate-900 dark:text-white ring-indigo-500/10 focus:ring-4 focus:border-indigo-500 focus:outline-none appearance-none cursor-pointer">
            {options.map((opt: string) => <option key={opt}>{opt}</option>)}
         </select>
      ) : (
         <input
           type={type}
           placeholder={placeholder}
           defaultValue={defaultValue}
           className="w-full h-14 px-6 border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 text-sm font-bold text-slate-900 dark:text-white ring-indigo-500/10 focus:ring-4 focus:border-indigo-500 focus:outline-none"
         />
      )}
    </div>
  );
}

function SaveButton({ saved, onClick, label = "Synchronize changes" }: any) {
   return (
      <button
         onClick={onClick}
         className={cn(
           "flex items-center gap-3 px-8 py-4 rounded-2xl font-black text-xs uppercase tracking-widest transition-all shadow-xl active:scale-95",
           saved
             ? "bg-emerald-600 text-white shadow-emerald-500/20"
             : "bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-slate-900/20"
         )}
       >
         {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
         {saved ? "Synchronized" : label}
       </button>
   );
}

function NeuralIcon({ className }: any) {
   return <Zap className={className} />;
}
