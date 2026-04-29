"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import {
  ShieldCheck, AlertTriangle, CheckCircle2, Clock, FileText,
  Globe, Building2, Lock, ChevronDown, ChevronRight,
  RefreshCw, Download, Eye, Users, Database,
} from "lucide-react";

type Framework = "SOX" | "GDPR" | "SOC2";

interface Control {
  id: string;
  domain: string;
  control: string;
  description: string;
  frequency: string;
  automated: boolean;
  status: "pass" | "fail" | "manual";
  findings: string;
}

interface GDPRCategory {
  id: string;
  category: string;
  data_types: string[];
  purpose: string;
  lawful_basis: string;
  retention_days: number;
  third_party_sharing: string[];
  dpo_reviewed: boolean;
}

const SOX_CONTROLS: Control[] = [
  { id: "SOX-AR1.1", domain: "Audit Trail", control: "Immutable Audit Log", description: "All financial changes logged with SHA-256 hash.", frequency: "continuous", automated: true, status: "pass", findings: "2,847 audit events on record with intact hashes." },
  { id: "SOX-AR1.2", domain: "Audit Trail", control: "Tamper Detection", description: "Hash verification of all audit records.", frequency: "quarterly", automated: true, status: "pass", findings: "Last tamper check: PASS. All 500 recent events verified." },
  { id: "SOX-FC1.1", domain: "Financial Close", control: "Month-End Close Checklist", description: "Documented close procedures completed and approved.", frequency: "monthly", automated: true, status: "pass", findings: "April 2026 close period: VALIDATED." },
  { id: "SOX-FC1.2", domain: "Financial Close", control: "Journal Entry Review", description: "All manual JEs reviewed and approved before posting.", frequency: "monthly", automated: true, status: "pass", findings: "14 journal entries reviewed and approved this month." },
  { id: "SOX-FC2.1", domain: "Financial Reporting", control: "Revenue Recognition", description: "Revenue recognized per ASC 606 with documented contracts.", frequency: "monthly", automated: true, status: "pass", findings: "Revenue schedule reconciled. 3 contracts on file." },
  { id: "SOX-AC1.1", domain: "Access Controls", control: "Privileged Access Review", description: "Quarterly review of privileged user access.", frequency: "quarterly", automated: true, status: "pass", findings: "6 admin users reviewed. 0 unauthorized access detected." },
  { id: "SOX-AC1.2", domain: "Access Controls", control: "Segregation of Duties", description: "No single user can approve and post journal entries.", frequency: "continuous", automated: true, status: "pass", findings: "Role matrix enforced. No SoD violations detected." },
  { id: "SOX-PO1.1", domain: "Procure-to-Pay", control: "3-Way PO Match", description: "POs matched against receipts and invoices before payment.", frequency: "continuous", automated: true, status: "pass", findings: "47 POs with completed 3-way matching." },
  { id: "SOX-IT1.1", domain: "IT Controls", control: "Change Management", description: "Production changes reviewed and approved before deploy.", frequency: "per-change", automated: false, status: "manual", findings: "Requires manual evidence: PR reviews and deploy approvals." },
  { id: "SOX-CC1.1", domain: "Control Environment", control: "Tone at the Top", description: "Board demonstrates commitment to integrity and ethics.", frequency: "annual", automated: false, status: "manual", findings: "Requires board meeting minutes and code of conduct sign-offs." },
];

const GDPR_DATA: GDPRCategory[] = [
  { id: "GDPR-DC1", category: "Customer Identity", data_types: ["name", "email", "company", "phone"], purpose: "Contract fulfillment & invoicing", lawful_basis: "Contract (Art 6.1.b)", retention_days: 2555, third_party_sharing: ["Stripe", "SendGrid"], dpo_reviewed: true },
  { id: "GDPR-DC2", category: "Financial Transactions", data_types: ["invoice amounts", "payment history", "bank details"], purpose: "Financial reporting & compliance", lawful_basis: "Legal obligation (Art 6.1.c)", retention_days: 2555, third_party_sharing: ["Stripe"], dpo_reviewed: true },
  { id: "GDPR-DC3", category: "Employee Payroll", data_types: ["salary", "bank account", "tax ID", "address"], purpose: "Payroll processing & tax", lawful_basis: "Contract + Legal obligation", retention_days: 2555, third_party_sharing: ["Tax Authority"], dpo_reviewed: true },
  { id: "GDPR-DC4", category: "Usage Analytics", data_types: ["login timestamps", "feature usage", "IP addresses"], purpose: "Security & fraud prevention", lawful_basis: "Legitimate interest (Art 6.1.f)", retention_days: 90, third_party_sharing: [], dpo_reviewed: true },
  { id: "GDPR-DC5", category: "Vendor / Supplier", data_types: ["contact name", "email", "bank details"], purpose: "Accounts payable & procurement", lawful_basis: "Contract (Art 6.1.b)", retention_days: 2555, third_party_sharing: [], dpo_reviewed: true },
];

const FRAMEWORK_SCORES = { SOX: 92, GDPR: 88, SOC2: 90 };
const FRAMEWORK_ICONS: Record<Framework, React.ElementType> = { SOX: Building2, GDPR: Globe, SOC2: ShieldCheck };
const FRAMEWORK_COLORS: Record<Framework, string> = {
  SOX: "text-blue-600 bg-blue-50 border-blue-200",
  GDPR: "text-violet-600 bg-violet-50 border-violet-200",
  SOC2: "text-emerald-600 bg-emerald-50 border-emerald-200",
};

export default function RegulatoryPage() {
  const { openChat } = useAppStore();
  const [activeTab, setActiveTab] = useState<Framework>("SOX");
  const [expandedDomains, setExpandedDomains] = useState<Set<string>>(new Set(["Audit Trail", "Financial Close"]));
  const [running, setRunning] = useState(false);

  const toggleDomain = (domain: string) => {
    setExpandedDomains(prev => {
      const n = new Set(prev);
      n.has(domain) ? n.delete(domain) : n.add(domain);
      return n;
    });
  };

  const handleRunTests = () => {
    setRunning(true);
    setTimeout(() => setRunning(false), 2000);
  };

  const domains = [...new Set(SOX_CONTROLS.map(c => c.domain))];
  const passCount = SOX_CONTROLS.filter(c => c.status === "pass").length;
  const failCount = SOX_CONTROLS.filter(c => c.status === "fail").length;
  const manualCount = SOX_CONTROLS.filter(c => c.status === "manual").length;

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Regulatory Compliance" />
      <div className="max-w-5xl mx-auto px-6 pt-6 space-y-6">

        {/* Framework Scores */}
        <div className="grid grid-cols-3 gap-4">
          {(["SOX", "GDPR", "SOC2"] as Framework[]).map(fw => {
            const Icon = FRAMEWORK_ICONS[fw];
            const score = FRAMEWORK_SCORES[fw];
            const colorClass = FRAMEWORK_COLORS[fw];
            return (
              <button
                key={fw}
                onClick={() => setActiveTab(fw)}
                className={cn(
                  "bg-white border rounded-2xl p-5 text-left transition-all",
                  activeTab === fw ? colorClass + " ring-2 ring-current" : "border-[#e8ddd4] hover:border-[#b3622d]"
                )}
              >
                <div className="flex items-center justify-between mb-3">
                  <Icon className={cn("w-5 h-5", FRAMEWORK_COLORS[fw].split(" ")[0])} />
                  <span className={cn(
                    "text-xs font-bold px-2 py-0.5 rounded-full",
                    score >= 85 ? "text-emerald-700 bg-emerald-100" : score >= 70 ? "text-amber-700 bg-amber-100" : "text-red-700 bg-red-100"
                  )}>
                    {score >= 85 ? "Compliant" : score >= 70 ? "At Risk" : "Non-Compliant"}
                  </span>
                </div>
                <div className="text-lg font-black text-[#1d1b17] mb-1">{fw}</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-[#f0e8e0] rounded-full h-2 overflow-hidden">
                    <div
                      className={cn("h-2 rounded-full", score >= 85 ? "bg-emerald-500" : score >= 70 ? "bg-amber-500" : "bg-red-500")}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                  <span className="text-sm font-black text-[#1d1b17]">{score}%</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        {activeTab === "SOX" && (
          <div className="space-y-4">
            {/* SOX Summary */}
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: "Total Controls", value: SOX_CONTROLS.length, color: "text-[#1d1b17]" },
                { label: "Automated Pass", value: passCount, color: "text-emerald-600" },
                { label: "Manual Required", value: manualCount, color: "text-amber-600" },
                { label: "Failed", value: failCount, color: failCount > 0 ? "text-red-600" : "text-gray-400" },
              ].map(({ label, value, color }) => (
                <div key={label} className="bg-white border border-[#e8ddd4] rounded-xl p-3 text-center">
                  <div className={cn("text-xl font-black", color)}>{value}</div>
                  <div className="text-[10px] text-[#8a7e74] uppercase">{label}</div>
                </div>
              ))}
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleRunTests}
                className="flex items-center gap-2 px-4 py-2 bg-[#b3622d] hover:bg-[#9d4f22] text-white rounded-xl text-sm font-semibold transition-all"
              >
                <RefreshCw className={cn("w-4 h-4", running && "animate-spin")} />
                {running ? "Running Tests..." : "Run All Automated Tests"}
              </button>
              <button
                onClick={() => openChat("Summarize my SOX compliance status and identify the highest priority gaps.")}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-[#e8ddd4] hover:border-[#b3622d] text-[#1d1b17] rounded-xl text-sm font-semibold transition-all"
              >
                <Eye className="w-4 h-4" /> SOX Analysis
              </button>
            </div>

            {/* Controls by Domain */}
            {domains.map(domain => {
              const domainControls = SOX_CONTROLS.filter(c => c.domain === domain);
              const isExpanded = expandedDomains.has(domain);
              const domainPass = domainControls.filter(c => c.status === "pass").length;
              return (
                <div key={domain} className="bg-white border border-[#e8ddd4] rounded-2xl overflow-hidden">
                  <button
                    onClick={() => toggleDomain(domain)}
                    className="w-full flex items-center justify-between p-4 hover:bg-[#faf8f5]"
                  >
                    <div className="flex items-center gap-3">
                      <div className="text-sm font-bold text-[#1d1b17]">{domain}</div>
                      <span className="text-[10px] text-[#8a7e74]">{domainControls.length} controls</span>
                      <span className={cn("text-[10px] font-semibold px-2 py-0.5 rounded-full", domainPass === domainControls.length ? "text-emerald-700 bg-emerald-100" : "text-amber-700 bg-amber-100")}>
                        {domainPass}/{domainControls.length} pass
                      </span>
                    </div>
                    {isExpanded ? <ChevronDown className="w-4 h-4 text-[#8a7e74]" /> : <ChevronRight className="w-4 h-4 text-[#8a7e74]" />}
                  </button>
                  {isExpanded && (
                    <div className="border-t border-[#f0e8e0] divide-y divide-[#f0e8e0]">
                      {domainControls.map(ctrl => (
                        <div key={ctrl.id} className="flex items-start gap-4 p-4">
                          <div className="mt-0.5">
                            {ctrl.status === "pass" && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                            {ctrl.status === "fail" && <AlertTriangle className="w-4 h-4 text-red-600" />}
                            {ctrl.status === "manual" && <Clock className="w-4 h-4 text-amber-500" />}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-0.5">
                              <span className="font-semibold text-sm text-[#1d1b17]">{ctrl.control}</span>
                              <span className="text-[9px] font-mono text-[#8a7e74]">{ctrl.id}</span>
                              {ctrl.automated && <span className="text-[10px] text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded-full font-semibold">Auto</span>}
                            </div>
                            <div className="text-xs text-[#6a6054] mb-1">{ctrl.description}</div>
                            <div className={cn(
                              "text-[11px] font-medium",
                              ctrl.status === "pass" ? "text-emerald-600" : ctrl.status === "fail" ? "text-red-600" : "text-amber-600"
                            )}>
                              {ctrl.findings}
                            </div>
                          </div>
                          <div className="text-[10px] text-[#8a7e74] shrink-0">{ctrl.frequency}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {activeTab === "GDPR" && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "Data Categories", value: GDPR_DATA.length, icon: Database, color: "text-violet-600" },
                { label: "DPO Reviewed", value: GDPR_DATA.filter(d => d.dpo_reviewed).length, icon: CheckCircle2, color: "text-emerald-600" },
                { label: "EU Transfers", value: GDPR_DATA.filter(d => d.third_party_sharing.length > 0).length, icon: Globe, color: "text-blue-600" },
              ].map(({ label, value, icon: Icon, color }) => (
                <div key={label} className="bg-white border border-[#e8ddd4] rounded-xl p-3 flex items-center gap-3">
                  <Icon className={cn("w-5 h-5", color)} />
                  <div>
                    <div className="text-xl font-black text-[#1d1b17]">{value}</div>
                    <div className="text-xs text-[#8a7e74]">{label}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-white border border-[#e8ddd4] rounded-2xl overflow-hidden">
              <div className="p-4 border-b border-[#f0e8e0] flex items-center justify-between">
                <h3 className="font-bold text-sm">Record of Processing Activities (Art. 30 ROPA)</h3>
                <button className="flex items-center gap-1 text-xs text-[#b3622d] font-semibold hover:underline">
                  <Download className="w-3.5 h-3.5" /> Export ROPA
                </button>
              </div>
              <div className="divide-y divide-[#f0e8e0]">
                {GDPR_DATA.map(cat => (
                  <div key={cat.id} className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="font-semibold text-sm text-[#1d1b17]">{cat.category}</div>
                        <div className="text-xs text-[#6a6054] mt-0.5">{cat.purpose}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        {cat.dpo_reviewed && <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">DPO Reviewed</span>}
                        <span className="text-[10px] text-[#8a7e74]">{Math.round(cat.retention_days / 365)}yr retention</span>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-xs">
                      <div>
                        <div className="text-[10px] uppercase text-[#8a7e74] font-semibold mb-1">Lawful Basis</div>
                        <div className="text-[#1d1b17]">{cat.lawful_basis}</div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase text-[#8a7e74] font-semibold mb-1">Data Types</div>
                        <div className="flex flex-wrap gap-1">
                          {cat.data_types.slice(0, 3).map(t => (
                            <span key={t} className="text-[10px] bg-[#f6f3ee] text-[#6a6054] px-1.5 py-0.5 rounded">{t}</span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase text-[#8a7e74] font-semibold mb-1">3rd Party Sharing</div>
                        <div className="text-[#1d1b17]">{cat.third_party_sharing.length > 0 ? cat.third_party_sharing.join(", ") : "None"}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white border border-[#e8ddd4] rounded-2xl p-4">
              <h3 className="font-bold text-sm mb-3">Data Subject Rights (DSARs)</h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { right: "Access (Art. 15)", desc: "Provide copy of all data held" },
                  { right: "Erasure (Art. 17)", desc: "Delete personal data on request" },
                  { right: "Portability (Art. 20)", desc: "Export data in machine-readable format" },
                  { right: "Restriction (Art. 18)", desc: "Stop processing pending review" },
                ].map(({ right, desc }) => (
                  <div key={right} className="flex items-center gap-2 p-3 bg-[#f6f3ee] rounded-xl">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <div>
                      <div className="text-xs font-semibold text-[#1d1b17]">{right}</div>
                      <div className="text-[10px] text-[#6a6054]">{desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "SOC2" && (
          <div className="space-y-4">
            <div className="grid grid-cols-5 gap-3">
              {["Security", "Availability", "Confidentiality", "Processing Integrity", "Privacy"].map(criteria => (
                <div key={criteria} className="bg-white border border-emerald-200 rounded-xl p-3 text-center">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 mx-auto mb-1" />
                  <div className="text-[10px] font-semibold text-[#1d1b17] leading-tight">{criteria}</div>
                  <div className="text-[9px] text-emerald-600 mt-0.5">In Scope</div>
                </div>
              ))}
            </div>

            <div className="bg-white border border-[#e8ddd4] rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="font-bold text-sm text-[#1d1b17]">SOC 2 Type II Status</div>
                  <div className="text-xs text-[#6a6054] mt-0.5">Last audit: January 2026 · Next surveillance: July 2026</div>
                </div>
                <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full">Compliant</span>
              </div>
              <div className="space-y-3">
                {[
                  { label: "Immutable Audit Log", status: "pass", detail: "SHA-256 hash chain verified — 2,847 events sealed." },
                  { label: "Tamper Detection", status: "pass", detail: "All audit records rehashed — no modifications detected." },
                  { label: "Access Control Reviews", status: "pass", detail: "6 privileged users reviewed Q1 2026." },
                  { label: "Encryption at Rest", status: "pass", detail: "PostgreSQL TDE enabled + AES-256 for backups." },
                  { label: "Incident Response Plan", status: "manual", detail: "Manual review required — update runbook annually." },
                  { label: "Penetration Testing", status: "manual", detail: "Annual pentest due Q3 2026." },
                ].map(({ label, status, detail }) => (
                  <div key={label} className="flex items-start gap-3 p-3 bg-[#f6f3ee] rounded-xl">
                    {status === "pass"
                      ? <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                      : <Clock className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />}
                    <div>
                      <div className="text-xs font-semibold text-[#1d1b17]">{label}</div>
                      <div className="text-[10px] text-[#6a6054]">{detail}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
