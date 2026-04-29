"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import {
  Palette, Globe, Zap, Building2, CheckCircle2, Settings,
  Copy, ExternalLink, Image, Code, Users, BarChart3,
  Shield, Brain, Mic, Link2, RefreshCw, Plus,
} from "lucide-react";

interface Tenant {
  id: string;
  name: string;
  subdomain: string;
  plan: "starter" | "growth" | "enterprise";
  status: "active" | "suspended";
  users: number;
  branding: {
    app_name: string;
    primary_color: string;
    logo_url: string | null;
    hide_powered_by: boolean;
  };
  custom_domain: string | null;
  features: Record<string, boolean>;
}

const DEMO_TENANTS: Tenant[] = [
  {
    id: "t1", name: "FinanceFlow Pro", subdomain: "financeflow", plan: "enterprise", status: "active", users: 18,
    branding: { app_name: "FinanceFlow Pro", primary_color: "#1a56db", logo_url: null, hide_powered_by: true },
    custom_domain: "app.financeflow.io",
    features: { ai_agent: true, forecasting: true, anomaly_detection: true, blockchain_audit: true, voice_commands: true, ml_marketplace: true, multi_currency: true, erp_sync: true, consolidation: true, investor_portal: true },
  },
  {
    id: "t2", name: "Acme Corp CFO", subdomain: "acmecfo", plan: "growth", status: "active", users: 7,
    branding: { app_name: "Acme CFO", primary_color: "#059669", logo_url: null, hide_powered_by: false },
    custom_domain: null,
    features: { ai_agent: true, forecasting: true, anomaly_detection: true, blockchain_audit: false, voice_commands: true, ml_marketplace: false, multi_currency: true, erp_sync: true, consolidation: false, investor_portal: false },
  },
  {
    id: "t3", name: "Startup Tracker", subdomain: "startuptrack", plan: "starter", status: "active", users: 3,
    branding: { app_name: "Startup Tracker", primary_color: "#7c3aed", logo_url: null, hide_powered_by: false },
    custom_domain: null,
    features: { ai_agent: true, forecasting: true, anomaly_detection: false, blockchain_audit: false, voice_commands: false, ml_marketplace: false, multi_currency: false, erp_sync: false, consolidation: false, investor_portal: true },
  },
];

const ALL_FEATURES = [
  { key: "ai_agent", label: "AI CFO Agent", icon: Brain },
  { key: "forecasting", label: "ML Forecasting", icon: BarChart3 },
  { key: "anomaly_detection", label: "Anomaly Detection", icon: Shield },
  { key: "blockchain_audit", label: "Blockchain Audit", icon: Link2 },
  { key: "voice_commands", label: "Voice Commands", icon: Mic },
  { key: "ml_marketplace", label: "ML Marketplace", icon: Zap },
  { key: "multi_currency", label: "Multi-Currency", icon: Globe },
  { key: "erp_sync", label: "ERP Sync", icon: RefreshCw },
  { key: "consolidation", label: "Consolidation", icon: Building2 },
  { key: "investor_portal", label: "Investor Portal", icon: Users },
];

const PLAN_COLORS = {
  starter: "text-gray-600 bg-gray-100",
  growth: "text-blue-700 bg-blue-100",
  enterprise: "text-violet-700 bg-violet-100",
};

export default function WhiteLabelPage() {
  const { openChat } = useAppStore();
  const [tenants, setTenants] = useState<Tenant[]>(DEMO_TENANTS);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(DEMO_TENANTS[0]);
  const [activeSection, setActiveSection] = useState<"branding" | "features" | "domain">("branding");
  const [copied, setCopied] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [newName, setNewName] = useState("");

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleColorChange = (color: string) => {
    if (!selectedTenant) return;
    const updated = { ...selectedTenant, branding: { ...selectedTenant.branding, primary_color: color } };
    setSelectedTenant(updated);
    setTenants(prev => prev.map(t => t.id === updated.id ? updated : t));
  };

  const handleFeatureToggle = (featureKey: string) => {
    if (!selectedTenant) return;
    const updated = {
      ...selectedTenant,
      features: { ...selectedTenant.features, [featureKey]: !selectedTenant.features[featureKey] },
    };
    setSelectedTenant(updated);
    setTenants(prev => prev.map(t => t.id === updated.id ? updated : t));
  };

  const handleProvision = () => {
    if (!newName.trim()) return;
    const subdomain = newName.toLowerCase().replace(/\s+/g, "-");
    const newTenant: Tenant = {
      id: Date.now().toString(),
      name: newName,
      subdomain,
      plan: "starter",
      status: "active",
      users: 0,
      branding: { app_name: newName, primary_color: "#b3622d", logo_url: null, hide_powered_by: false },
      custom_domain: null,
      features: Object.fromEntries(ALL_FEATURES.map(f => [f.key, f.key === "ai_agent" || f.key === "forecasting"])),
    };
    setTenants(prev => [...prev, newTenant]);
    setSelectedTenant(newTenant);
    setNewName("");
    setShowNew(false);
  };

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="White-Label Platform" />
      <div className="max-w-6xl mx-auto px-6 pt-6">
        <div className="grid grid-cols-[280px_1fr] gap-6">

          {/* Tenant List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-[#1d1b17]">Tenants ({tenants.length})</h3>
              <button
                onClick={() => setShowNew(true)}
                className="flex items-center gap-1 text-xs font-semibold text-[#b3622d] hover:underline"
              >
                <Plus className="w-3 h-3" /> New
              </button>
            </div>

            {showNew && (
              <div className="bg-white border border-[#e8ddd4] rounded-xl p-3 space-y-2">
                <input
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                  placeholder="Tenant name..."
                  className="w-full text-xs border border-[#e8ddd4] rounded-lg px-2 py-1.5 focus:outline-none focus:border-[#b3622d]"
                  onKeyDown={e => e.key === "Enter" && handleProvision()}
                  autoFocus
                />
                <div className="flex gap-2">
                  <button onClick={handleProvision} className="flex-1 text-xs bg-[#b3622d] text-white rounded-lg py-1.5 font-semibold">Provision</button>
                  <button onClick={() => setShowNew(false)} className="text-xs text-[#6a6054] px-2">Cancel</button>
                </div>
              </div>
            )}

            {tenants.map(tenant => (
              <button
                key={tenant.id}
                onClick={() => setSelectedTenant(tenant)}
                className={cn(
                  "w-full text-left bg-white border rounded-2xl p-4 transition-all",
                  selectedTenant?.id === tenant.id ? "border-[#b3622d] ring-1 ring-[#b3622d]/20" : "border-[#e8ddd4] hover:border-[#b3622d]/50"
                )}
              >
                <div className="flex items-start justify-between mb-2">
                  <div
                    className="w-8 h-8 rounded-xl flex items-center justify-center text-white font-black text-sm"
                    style={{ backgroundColor: tenant.branding.primary_color }}
                  >
                    {tenant.branding.app_name[0]}
                  </div>
                  <span className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded-full capitalize", PLAN_COLORS[tenant.plan])}>
                    {tenant.plan}
                  </span>
                </div>
                <div className="font-bold text-xs text-[#1d1b17]">{tenant.name}</div>
                <div className="text-[10px] text-[#8a7e74] mt-0.5">{tenant.subdomain}.vireon.ai</div>
                <div className="flex items-center gap-2 mt-2">
                  <Users className="w-3 h-3 text-[#b0a499]" />
                  <span className="text-[10px] text-[#8a7e74]">{tenant.users} users</span>
                  <div className={cn("w-1.5 h-1.5 rounded-full ml-auto", tenant.status === "active" ? "bg-emerald-500" : "bg-red-500")} />
                </div>
              </button>
            ))}
          </div>

          {/* Detail Panel */}
          {selectedTenant && (
            <div className="space-y-4">
              {/* Header */}
              <div className="bg-white border border-[#e8ddd4] rounded-2xl p-5">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-black text-lg"
                      style={{ backgroundColor: selectedTenant.branding.primary_color }}
                    >
                      {selectedTenant.branding.app_name[0]}
                    </div>
                    <div>
                      <div className="font-black text-lg text-[#1d1b17]">{selectedTenant.name}</div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-sm text-[#6a6054]">{selectedTenant.subdomain}.vireon.ai</span>
                        {selectedTenant.custom_domain && (
                          <span className="text-[11px] text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full font-semibold">
                            {selectedTenant.custom_domain}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleCopy(`https://${selectedTenant.subdomain}.vireon.ai`)}
                      className="flex items-center gap-1 text-xs text-[#6a6054] border border-[#e8ddd4] rounded-lg px-2 py-1.5 hover:border-[#b3622d] transition-all"
                    >
                      {copied ? <CheckCircle2 className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                      {copied ? "Copied!" : "Copy URL"}
                    </button>
                    <span className={cn("text-xs font-bold px-2 py-1 rounded-lg capitalize", PLAN_COLORS[selectedTenant.plan])}>
                      {selectedTenant.plan}
                    </span>
                  </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-1">
                  {(["branding", "features", "domain"] as const).map(tab => (
                    <button
                      key={tab}
                      onClick={() => setActiveSection(tab)}
                      className={cn(
                        "px-3 py-1.5 rounded-xl text-xs font-semibold transition-all capitalize",
                        activeSection === tab ? "bg-[#b3622d] text-white" : "text-[#6a6054] hover:bg-[#f6f3ee]"
                      )}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </div>

              {/* Branding */}
              {activeSection === "branding" && (
                <div className="bg-white border border-[#e8ddd4] rounded-2xl p-5 space-y-4">
                  <h3 className="font-bold text-sm flex items-center gap-2">
                    <Palette className="w-4 h-4 text-[#b3622d]" /> Branding
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-[11px] font-semibold text-[#8a7e74] uppercase mb-1.5 block">App Name</label>
                      <input
                        defaultValue={selectedTenant.branding.app_name}
                        className="w-full text-sm border border-[#e8ddd4] rounded-xl px-3 py-2 focus:outline-none focus:border-[#b3622d]"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-[#8a7e74] uppercase mb-1.5 block">Primary Color</label>
                      <div className="flex items-center gap-2">
                        <input
                          type="color"
                          value={selectedTenant.branding.primary_color}
                          onChange={e => handleColorChange(e.target.value)}
                          className="w-10 h-9 rounded-xl border border-[#e8ddd4] cursor-pointer"
                        />
                        <span className="text-sm font-mono text-[#6a6054]">{selectedTenant.branding.primary_color}</span>
                      </div>
                    </div>
                  </div>
                  <div>
                    <label className="text-[11px] font-semibold text-[#8a7e74] uppercase mb-1.5 block">Logo Upload</label>
                    <div className="border-2 border-dashed border-[#e8ddd4] rounded-xl p-6 text-center hover:border-[#b3622d] transition-all cursor-pointer">
                      <Image className="w-6 h-6 text-[#b0a499] mx-auto mb-2" />
                      <div className="text-xs text-[#6a6054]">Drop logo here or click to upload (SVG, PNG · max 500KB)</div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-[#f6f3ee] rounded-xl">
                    <div>
                      <div className="text-sm font-semibold text-[#1d1b17]">Hide "Powered by Vireon"</div>
                      <div className="text-xs text-[#6a6054]">Remove branding attribution from footer and login page</div>
                    </div>
                    <button
                      onClick={() => {
                        const updated = { ...selectedTenant, branding: { ...selectedTenant.branding, hide_powered_by: !selectedTenant.branding.hide_powered_by } };
                        setSelectedTenant(updated);
                        setTenants(prev => prev.map(t => t.id === updated.id ? updated : t));
                      }}
                      className={cn("w-10 h-5 rounded-full transition-all", selectedTenant.branding.hide_powered_by ? "bg-[#b3622d]" : "bg-[#d8c9be]")}
                    >
                      <div className={cn("w-4 h-4 bg-white rounded-full shadow transition-all mx-0.5", selectedTenant.branding.hide_powered_by ? "translate-x-5" : "translate-x-0")} />
                    </button>
                  </div>

                  {/* Preview */}
                  <div>
                    <label className="text-[11px] font-semibold text-[#8a7e74] uppercase mb-1.5 block">Preview</label>
                    <div className="border border-[#e8ddd4] rounded-xl p-4 bg-white">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-6 h-6 rounded-lg flex items-center justify-center text-white text-xs font-black" style={{ backgroundColor: selectedTenant.branding.primary_color }}>
                          {selectedTenant.branding.app_name[0]}
                        </div>
                        <span className="font-bold text-sm" style={{ color: selectedTenant.branding.primary_color }}>
                          {selectedTenant.branding.app_name}
                        </span>
                      </div>
                      <div className="h-px bg-[#f0e8e0] mb-3" />
                      <div className="flex gap-2">
                        <div className="px-3 py-1.5 rounded-lg text-xs text-white font-semibold" style={{ backgroundColor: selectedTenant.branding.primary_color }}>Dashboard</div>
                        <div className="px-3 py-1.5 rounded-lg text-xs text-[#6a6054] bg-[#f6f3ee] font-semibold">Reports</div>
                        <div className="px-3 py-1.5 rounded-lg text-xs text-[#6a6054] bg-[#f6f3ee] font-semibold">Analytics</div>
                      </div>
                      {!selectedTenant.branding.hide_powered_by && (
                        <div className="text-[9px] text-[#b0a499] mt-3 text-center">Powered by Vireon</div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Features */}
              {activeSection === "features" && (
                <div className="bg-white border border-[#e8ddd4] rounded-2xl p-5">
                  <h3 className="font-bold text-sm flex items-center gap-2 mb-4">
                    <Zap className="w-4 h-4 text-[#b3622d]" /> Feature Flags
                  </h3>
                  <div className="grid grid-cols-2 gap-3">
                    {ALL_FEATURES.map(({ key, label, icon: Icon }) => {
                      const enabled = selectedTenant.features[key] ?? false;
                      return (
                        <div
                          key={key}
                          className={cn("flex items-center justify-between p-3 rounded-xl border transition-all", enabled ? "border-[#b3622d]/30 bg-[#fdf5ee]" : "border-[#e8ddd4] bg-[#fafaf8]")}
                        >
                          <div className="flex items-center gap-2">
                            <Icon className={cn("w-4 h-4", enabled ? "text-[#b3622d]" : "text-[#b0a499]")} />
                            <span className="text-xs font-semibold text-[#1d1b17]">{label}</span>
                          </div>
                          <button
                            onClick={() => handleFeatureToggle(key)}
                            className={cn("w-9 h-5 rounded-full transition-all shrink-0", enabled ? "bg-[#b3622d]" : "bg-[#d8c9be]")}
                          >
                            <div className={cn("w-4 h-4 bg-white rounded-full shadow transition-all mx-0.5", enabled ? "translate-x-4" : "translate-x-0")} />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Domain */}
              {activeSection === "domain" && (
                <div className="bg-white border border-[#e8ddd4] rounded-2xl p-5 space-y-4">
                  <h3 className="font-bold text-sm flex items-center gap-2">
                    <Globe className="w-4 h-4 text-[#b3622d]" /> Custom Domain
                  </h3>
                  <div className="p-3 bg-[#f6f3ee] rounded-xl">
                    <div className="text-[11px] uppercase font-semibold text-[#8a7e74] mb-1">Default URL</div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-mono text-[#1d1b17]">https://{selectedTenant.subdomain}.vireon.ai</span>
                      <button onClick={() => handleCopy(`https://${selectedTenant.subdomain}.vireon.ai`)} className="p-1 hover:bg-white rounded">
                        <Copy className="w-3 h-3 text-[#8a7e74]" />
                      </button>
                    </div>
                  </div>
                  {selectedTenant.custom_domain ? (
                    <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
                      <div className="flex items-center gap-2 mb-1">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <span className="text-sm font-semibold text-emerald-800">Custom Domain Active</span>
                      </div>
                      <div className="text-sm font-mono text-emerald-700">{selectedTenant.custom_domain}</div>
                      <div className="text-xs text-emerald-600 mt-1">SSL Certificate: Active (Let's Encrypt)</div>
                    </div>
                  ) : (
                    <div>
                      <label className="text-[11px] font-semibold text-[#8a7e74] uppercase mb-1.5 block">Custom Domain</label>
                      <input
                        placeholder="app.yourdomain.com"
                        className="w-full text-sm border border-[#e8ddd4] rounded-xl px-3 py-2 focus:outline-none focus:border-[#b3622d] mb-2"
                      />
                      <div className="space-y-2 p-3 bg-[#f6f3ee] rounded-xl">
                        {[
                          "Add CNAME record: app.yourdomain.com → cname.vireon.ai",
                          "Wait for DNS propagation (up to 48 hours)",
                          "SSL certificate auto-provisioned via Let's Encrypt",
                        ].map((step, i) => (
                          <div key={i} className="flex items-start gap-2 text-xs text-[#6a6054]">
                            <div className="w-4 h-4 rounded-full bg-[#b3622d] text-white font-bold text-[9px] flex items-center justify-center shrink-0 mt-0.5">{i + 1}</div>
                            {step}
                          </div>
                        ))}
                      </div>
                      <button className="mt-3 w-full py-2 bg-[#b3622d] text-white rounded-xl text-sm font-semibold hover:bg-[#9d4f22] transition-all">
                        Configure Domain
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
