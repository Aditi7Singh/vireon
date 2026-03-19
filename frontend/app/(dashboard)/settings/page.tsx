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
    <div className="min-h-screen bg-slate-950 pb-20">
      <TopBar title="Settings & Configuration" />

      <div className="p-8 max-w-[1600px] mx-auto">
        <div className="flex flex-col lg:flex-row gap-12">

          {/* Navigation */}
          <div className="lg:w-80 shrink-0 space-y-8">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold text-white tracking-tight">System <span className="text-slate-400">Settings</span></h1>
              <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                <Monitor className="w-3.5 h-3.5 text-indigo-500" />
                Platform Parameters
              </div>
            </div>

            <nav className="space-y-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "w-full group flex items-start gap-4 p-4 rounded-xl transition-all text-left border relative",
                    activeTab === tab.id
                      ? "bg-indigo-600/10 border-indigo-500/20 text-indigo-500"
                      : "border-transparent text-slate-500 hover:bg-slate-900 hover:border-slate-800"
                  )}
                >
                  <div className={cn(
                    "p-2 rounded-lg transition-all",
                    activeTab === tab.id ? "bg-indigo-600 text-white" : "bg-slate-800"
                  )}>
                    <tab.icon className="w-5 h-5" />
                  </div>
                  <div className="flex-grow min-w-0">
                    <p className={cn(
                      "text-[10px] font-bold uppercase tracking-wider",
                      activeTab === tab.id ? "text-white" : "text-slate-400 group-hover:text-slate-200"
                    )}>{tab.label}</p>
                    <p className="text-[10px] font-medium text-slate-600 truncate mt-0.5 uppercase tracking-wide">{tab.desc}</p>
                  </div>
                </button>
              ))}
            </nav>
          </div>

          {/* Form Area */}
          <div className="flex-1 space-y-12 max-w-4xl">
            {activeTab === "company" && (
              <div className="space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
                <div className="glass-card rounded-[48px] p-12 border-white/5 shadow-2xl">
                  <div className="flex items-center justify-between mb-8">
                    <div className="space-y-1">
                      <h2 className="text-2xl font-bold text-white tracking-tight">Entity Information</h2>
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Core administrative identity</p>
                    </div>
                    <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-500">
                      <Building2 className="w-6 h-6" />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <Field label="Organization Name" placeholder="Acme Global Inc" defaultValue="Acme Corp" />
                    <Field label="Industry Sector" type="select" options={['Technology', 'Finance', 'Logistics', 'Energy']} />
                    <Field label="Employee Count" type="select" options={['1-20', '21-100', '101-500', '500+']} />
                    <Field label="Fiscal Year End" type="select" options={['Jan-Dec', 'Apr-Mar', 'Jul-Jun']} />
                  </div>
                </div>

                <div className="glass-card rounded-2xl p-8 border-slate-800">
                  <h2 className="text-xl font-bold text-white tracking-tight mb-8">Regional Configuration</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <Field label="Default Currency" type="select" options={['USD ($)', 'EUR (€)', 'GBP (£)', 'INR (₹)']} />
                    <Field label="Time Zone" type="select" options={['UTC-5 (EST)', 'UTC-8 (PST)', 'UTC+0 (GMT)', 'UTC+5:30 (IST)']} />
                  </div>
                </div>

                <div className="flex items-center justify-end pt-8">
                  <SaveButton saved={saved} onClick={handleSave} />
                </div>
              </div>
            )}

            {activeTab === "integrations" && (
              <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="glass-card rounded-2xl p-8 border-slate-800">
                  <div className="flex items-center justify-between mb-8">
                    <div className="space-y-1">
                      <h2 className="text-2xl font-bold text-white tracking-tight">Connected Services</h2>
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Active data synchronization pipelines</p>
                    </div>
                    <RefreshCw className={cn("w-5 h-5 text-slate-500 transition-all", isSyncing && "animate-spin text-indigo-500")} />
                  </div>

                  <div className="space-y-4">
                    {[
                      { name: "QuickBooks", status: "Operational", icon: "📘" },
                      { name: "Stripe", status: "Operational", icon: "💳" },
                      { name: "Plaid", status: "Operational", icon: "🏦" },
                      { name: "Sage Intacct", status: "Disconnected", icon: "💎" },
                    ].map((integration) => (
                      <div
                        key={integration.name}
                        className="flex items-center justify-between p-6 bg-slate-900 rounded-xl border border-slate-800 group hover:border-slate-700 transition-all"
                      >
                        <div className="flex items-center gap-6">
                          <div className="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center text-xl border border-slate-700">
                            {integration.icon}
                          </div>
                          <div>
                            <p className="text-base font-bold text-white tracking-tight">{integration.name}</p>
                            <p className={cn(
                              "text-[10px] font-bold uppercase tracking-wider",
                              integration.status === "Operational" ? "text-emerald-500" : "text-slate-500"
                            )}>
                              {integration.status}
                            </p>
                          </div>
                        </div>
                        <button className="btn-secondary py-1.5 px-3 text-[10px]">
                          {integration.status === "Operational" ? "Configure" : "Connect"}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass-card rounded-2xl p-8 border-slate-800">
                  <h3 className="text-lg font-bold text-white tracking-tight mb-8">Data Sources</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {["Netsuite", "Xero", "Gusto", "Ramp", "Brex", "Bill.com"].map((name) => (
                      <button
                        key={name}
                        className="flex flex-col items-center justify-center gap-4 p-6 bg-slate-900 border border-slate-800 rounded-xl hover:border-indigo-500/50 hover:bg-slate-800/50 transition-all group"
                      >
                        <div className="w-12 h-12 bg-slate-800 rounded-lg flex items-center justify-center border border-slate-700 group-hover:bg-indigo-600 group-hover:border-indigo-500 transition-all">
                          <Cloud className="w-6 h-6 text-slate-400 group-hover:text-white" />
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 group-hover:text-white">{name}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === "rbac" && (
              <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="glass-card rounded-2xl p-8 border-slate-800">
                  <div className="flex items-center justify-between mb-8">
                    <div className="space-y-1">
                      <h2 className="text-2xl font-bold text-white tracking-tight">Access Control</h2>
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">User roles & permissions</p>
                    </div>
                    <button className="btn-primary py-2 px-4 text-[10px]">
                      <User className="w-3.5 h-3.5" />
                      Add Member
                    </button>
                  </div>

                  <div className="space-y-4">
                    {[
                      { name: "Aditi Singh", role: "Super Admin", email: "aditi@vireon.ai", avatar: "AS" },
                      { name: "Saurabh Garg", role: "Moderator", email: "saurabh@vireon.ai", avatar: "SG" },
                      { name: "Manoj Kumar", role: "Analyst", email: "manoj@vireon.ai", avatar: "MK" },
                    ].map((member) => (
                      <div key={member.email} className="flex items-center justify-between p-6 bg-slate-900 rounded-xl border border-slate-800 group hover:border-slate-700 transition-all">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-500 font-bold">
                            {member.avatar}
                          </div>
                          <div>
                            <p className="text-base font-bold text-white tracking-tight">{member.name}</p>
                            <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">{member.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-6">
                          <span className="text-[9px] font-bold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded">
                            {member.role}
                          </span>
                          <button className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-500 hover:text-white transition-all">
                            <ChevronRight className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass-card rounded-[48px] p-12 border-white/5 shadow-2xl">
                  <h3 className="text-2xl font-black text-white font-outfit tracking-tighter uppercase mb-10">Access Protocols</h3>
                  <div className="space-y-10">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <p className="text-xl font-black text-white font-outfit uppercase tracking-tight">Multi-Factor Authentication</p>
                        <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Enforce 2FA for all Super Admin accounts</p>
                      </div>
                      <div className="w-14 h-8 bg-indigo-600 rounded-full relative shadow-2xl shadow-indigo-600/30">
                        <div className="absolute right-1.5 top-1.5 w-5 h-5 bg-white rounded-full shadow-2xl" />
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <p className="text-xl font-black text-white font-outfit uppercase tracking-tight">Neural Isolation</p>
                        <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Prevent AI from accessing Payroll PII data nodes</p>
                      </div>
                      <div className="w-14 h-8 bg-indigo-600 rounded-full relative shadow-2xl shadow-indigo-600/30">
                        <div className="absolute right-1.5 top-1.5 w-5 h-5 bg-white rounded-full shadow-2xl" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "api" && (
              <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="glass-card rounded-2xl p-8 border-slate-800">
                  <div className="flex items-center justify-between mb-8">
                    <div className="space-y-1">
                      <h2 className="text-2xl font-bold text-white tracking-tight">API Infrastructure</h2>
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Secure external connection nodes</p>
                    </div>
                    <Zap className="w-6 h-6 text-amber-500" />
                  </div>

                  <div className="space-y-8">
                    <Field label="Groq API Key" type="password" defaultValue="gsk_neural_8b2c_locked" />
                    <Field label="OpenRouter Key" type="password" defaultValue="sk-or-v1-neural-gate" />
                    <Field label="Backend URI" placeholder="http://localhost:8000" defaultValue="http://localhost:8000" />
                  </div>
                </div>

                <div className="flex items-center justify-end pt-8">
                  <SaveButton saved={saved} onClick={handleSave} label="Update Keys" />
                </div>
              </div>
            )}

            {activeTab !== "company" && activeTab !== "integrations" && activeTab !== "api" && activeTab !== "rbac" && (
              <div className="glass-card rounded-2xl p-16 text-center border-slate-800 flex flex-col items-center justify-center">
                <Settings className="w-16 h-16 text-slate-800 mx-auto mb-8" />
                <h3 className="text-2xl font-bold text-white tracking-tight">
                  Module Configuration <br /> <span className="text-slate-500">Under Maintenance</span>
                </h3>
                <p className="text-slate-500 font-bold text-[10px] uppercase tracking-wider mt-4 max-w-sm">
                  This administrative module is currently being optimized for industrial deployment.
                </p>
                <button
                  onClick={() => setActiveTab('company')}
                  className="mt-8 text-[10px] font-bold uppercase tracking-wider text-indigo-500 hover:text-white transition-all underline underline-offset-4"
                >
                  Return to Dashboard
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
    <div className="space-y-4">
      <label className="block text-[9px] font-black uppercase tracking-[0.25em] text-slate-600">
        {label}
      </label>
      {type === "select" ? (
        <div className="relative group">
          <select className="w-full h-16 px-8 bg-white/5 border border-white/5 rounded-[24px] text-sm font-black text-white tracking-widest focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500/50 focus:outline-none appearance-none cursor-pointer transition-all duration-500 group-hover:bg-white/[0.08] uppercase">
            {options.map((opt: string) => <option key={opt} className="bg-[#020617] text-white">{opt}</option>)}
          </select>
          <div className="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none text-slate-600">
            <ChevronRight className="w-4 h-4 rotate-90" />
          </div>
        </div>
      ) : (
        <input
          type={type}
          placeholder={placeholder}
          defaultValue={defaultValue}
          className="w-full h-16 px-8 bg-white/5 border border-white/5 rounded-[24px] text-sm font-black text-white tracking-widest focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500/50 focus:outline-none transition-all duration-500 hover:bg-white/[0.08]"
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
        "flex items-center gap-4 px-10 py-5 rounded-2xl font-black text-[10px] uppercase tracking-[0.25em] transition-all duration-700 shadow-2xl active:scale-95",
        saved
          ? "bg-emerald-600 text-white shadow-emerald-500/20"
          : "bg-indigo-600 text-white shadow-indigo-600/20 hover:bg-indigo-500 hover:shadow-indigo-500/30"
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
