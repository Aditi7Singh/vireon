"use client";

import { useState, useEffect } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import api from "@/lib/api";
import {
  Package, Plus, Search, Sparkles, CheckCircle2, AlertCircle,
  Mail, FileText, X, Building2, Clock,
} from "lucide-react";

interface Vendor {
  id: string;
  name: string;
  category: string;
  contact: string;
  email: string;
  phone: string;
  website: string;
  ytd_spend: number;
  last_payment: string;
  payment_terms: string;
  status: "active" | "inactive" | "at_risk" | "preferred";
  w9_status: "on_file" | "missing" | "expired";
  risk_score: number;
  avg_days_to_pay: number;
  invoices_ytd: number;
}

const MOCK_VENDORS: Vendor[] = [
  { id: "1", name: "Amazon Web Services", category: "Infrastructure", contact: "AWS Support", email: "aws-billing@amazon.com", phone: "+1-800-379-7441", website: "aws.amazon.com", ytd_spend: 54200, last_payment: "2026-04-01", payment_terms: "Net 30", status: "preferred", w9_status: "on_file", risk_score: 12, avg_days_to_pay: 28, invoices_ytd: 4 },
  { id: "2", name: "Salesforce", category: "CRM / SaaS", contact: "Enterprise Account", email: "billing@salesforce.com", phone: "+1-800-667-6389", website: "salesforce.com", ytd_spend: 33600, last_payment: "2026-03-15", payment_terms: "Net 30", status: "active", w9_status: "on_file", risk_score: 18, avg_days_to_pay: 30, invoices_ytd: 4 },
  { id: "3", name: "Cooley LLP", category: "Legal", contact: "Partner Office", email: "billing@cooley.com", phone: "+1-650-843-5000", website: "cooley.com", ytd_spend: 67500, last_payment: "2026-03-01", payment_terms: "Net 15", status: "at_risk", w9_status: "on_file", risk_score: 68, avg_days_to_pay: 42, invoices_ytd: 3 },
  { id: "4", name: "WeWork", category: "Office Space", contact: "Enterprise Team", email: "enterprise@wework.com", phone: "+1-646-389-3922", website: "wework.com", ytd_spend: 39200, last_payment: "2026-04-12", payment_terms: "Net 1", status: "active", w9_status: "on_file", risk_score: 35, avg_days_to_pay: 1, invoices_ytd: 4 },
  { id: "5", name: "Datadog", category: "Monitoring", contact: "Support Team", email: "billing@datadoghq.com", phone: "+1-866-329-4466", website: "datadoghq.com", ytd_spend: 8400, last_payment: "2026-04-15", payment_terms: "Net 30", status: "preferred", w9_status: "on_file", risk_score: 8, avg_days_to_pay: 25, invoices_ytd: 4 },
  { id: "6", name: "Greenhouse Software", category: "HR / ATS", contact: "Customer Success", email: "billing@greenhouse.io", phone: "+1-646-677-7060", website: "greenhouse.io", ytd_spend: 14400, last_payment: "2026-02-28", payment_terms: "Net 30", status: "active", w9_status: "missing", risk_score: 22, avg_days_to_pay: 31, invoices_ytd: 4 },
  { id: "7", name: "Rippling", category: "HR / Payroll", contact: "Enterprise HR", email: "billing@rippling.com", phone: "+1-415-854-0048", website: "rippling.com", ytd_spend: 28800, last_payment: "2026-04-01", payment_terms: "Auto-debit", status: "preferred", w9_status: "on_file", risk_score: 5, avg_days_to_pay: 1, invoices_ytd: 4 },
  { id: "8", name: "Notion Labs", category: "Productivity", contact: "Billing", email: "billing@notion.so", phone: "+1-888-888-2946", website: "notion.so", ytd_spend: 1920, last_payment: "2026-04-01", payment_terms: "Auto-debit", status: "inactive", w9_status: "expired", risk_score: 45, avg_days_to_pay: 1, invoices_ytd: 4 },
];

const statusMeta = {
  preferred:  { label: "Preferred",  color: "#059669", bg: "#ecfdf5", border: "#a7f3d0" },
  active:     { label: "Active",     color: "#2563eb", bg: "#eff6ff", border: "#bfdbfe" },
  at_risk:    { label: "At Risk",    color: "#dc2626", bg: "#fef2f2", border: "#fecaca" },
  inactive:   { label: "Inactive",   color: "#6b7280", bg: "#f3f4f6", border: "#d1d5db" },
};

const w9Meta = {
  on_file:  { label: "On File",  color: "#059669", icon: CheckCircle2 },
  missing:  { label: "Missing",  color: "#dc2626", icon: AlertCircle },
  expired:  { label: "Expired",  color: "#d97706", icon: Clock },
};

export default function VendorsPage() {
  const { openChat } = useAppStore();
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [showNewModal, setShowNewModal] = useState(false);
  const [selectedVendor, setSelectedVendor] = useState<Vendor | null>(null);
  const [vendors, setVendors] = useState<Vendor[]>(MOCK_VENDORS);

  useEffect(() => {
    async function load() {
      try {
        const health = await api.getStartupHealth();
        const cid = health.default_company_id;
        if (!cid) return;
        const res = await api.getContacts(cid, { type: "VENDOR" });
        if (res.contacts.length > 0) {
          setVendors(res.contacts.map((c: import("@/lib/api").ContactRecord) => ({
            id: c.id,
            name: c.name,
            category: (c.billing_address as any)?.category || "Vendor",
            contact: c.name,
            email: c.email || "",
            phone: c.phone || "",
            website: "",
            ytd_spend: 0,
            last_payment: "",
            payment_terms: c.payment_terms || "Net 30",
            status: (c.status === "active" ? "active" : "inactive") as Vendor["status"],
            w9_status: "on_file" as Vendor["w9_status"],
            risk_score: 20,
            avg_days_to_pay: 30,
            invoices_ytd: 0,
          })));
        }
      } catch {
        // keep mock data on error
      }
    }
    load();
  }, []);

  const categories = ["all", ...Array.from(new Set(vendors.map(v => v.category)))];

  const filtered = vendors.filter(v => {
    const matchSearch = v.name.toLowerCase().includes(search.toLowerCase());
    const matchCat = categoryFilter === "all" || v.category === categoryFilter;
    return matchSearch && matchCat;
  });

  const ytdTotal = vendors.reduce((s, v) => s + v.ytd_spend, 0);
  const atRiskCount = vendors.filter(v => v.status === "at_risk").length;
  const missingW9 = vendors.filter(v => v.w9_status !== "on_file").length;

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Vendors" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Package className="h-3.5 w-3.5" /> Vendor Management
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Vendor Directory</h1>
              <p className="mt-1 text-sm text-[#5f5344]">Manage vendors, track spend, payment terms, W-9 compliance, and risk scores.</p>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => openChat("Identify vendor concentration risk and suggest diversification")} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <Sparkles className="h-4 w-4" /> Risk Analysis
              </button>
              <button onClick={() => setShowNewModal(true)} className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                <Plus className="h-4 w-4" /> Add Vendor
              </button>
            </div>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Total Vendors", value: vendors.length.toString(), sub: `${vendors.filter(v => v.status === "preferred").length} preferred` },
            { label: "YTD Spend", value: formatCurrency(ytdTotal), sub: "Across all vendors" },
            { label: "W-9 Issues", value: missingW9.toString(), sub: `${missingW9} need attention`, color: missingW9 > 0 ? "text-amber-700" : "text-emerald-700" },
            { label: "At Risk", value: atRiskCount.toString(), sub: "Concentration or late pay", color: atRiskCount > 0 ? "text-red-600" : "text-emerald-700" },
          ].map((s) => (
            <article key={s.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{s.label}</p>
              <p className={cn("mt-2 text-2xl font-bold", s.color || "text-[#2a2017]")}>{s.value}</p>
              <p className="mt-1 text-xs text-[#9a8872]">{s.sub}</p>
            </article>
          ))}
        </section>

        {/* Filters + Cards */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between border-b border-[#ede8e0]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9a8872]" />
              <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search vendors..." className="rounded-xl border border-[#ddd2c2] bg-[#f9f6f1] py-2 pl-9 pr-4 text-sm w-64 outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {categories.map(c => (
                <button key={c} onClick={() => setCategoryFilter(c)} className={cn("rounded-full px-3 py-1 text-xs font-semibold border capitalize transition-all", categoryFilter === c ? "bg-[#231c15] text-white border-[#231c15]" : "bg-white border-[#ddd2c2] text-[#776b5a] hover:border-[#b8a898]")}>
                  {c === "all" ? "All Categories" : c}
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((vendor) => {
              const sStatus = statusMeta[vendor.status];
              const w9 = w9Meta[vendor.w9_status];
              const W9Icon = w9.icon;
              return (
                <div key={vendor.id} onClick={() => setSelectedVendor(vendor)} className="rounded-xl border border-[#ede8e0] p-4 hover:border-[#cbb7a1] hover:shadow-md transition-all cursor-pointer bg-white">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 rounded-xl bg-[#f0ebe3] flex items-center justify-center shrink-0">
                        <Building2 className="h-5 w-5 text-[#8d4f27]" />
                      </div>
                      <div>
                        <p className="font-bold text-[#2a2017] text-sm">{vendor.name}</p>
                        <p className="text-xs text-[#776b5a]">{vendor.category}</p>
                      </div>
                    </div>
                    <span className="rounded-full px-2 py-0.5 text-xs font-semibold border" style={{ color: sStatus.color, background: sStatus.bg, borderColor: sStatus.border }}>
                      {sStatus.label}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 mt-3">
                    <div>
                      <p className="text-xs text-[#9a8872]">YTD Spend</p>
                      <p className="text-sm font-bold text-[#2a2017]">{formatCurrency(vendor.ytd_spend)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-[#9a8872]">Terms</p>
                      <p className="text-sm font-semibold text-[#5f5344]">{vendor.payment_terms}</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-[#f0ebe3]">
                    <div className="flex items-center gap-1.5">
                      <W9Icon className="h-3.5 w-3.5" style={{ color: w9.color }} />
                      <span className="text-xs font-medium" style={{ color: w9.color }}>W-9 {w9.label}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs text-[#776b5a]">Risk:</span>
                      <span className={cn("text-xs font-bold", vendor.risk_score < 25 ? "text-emerald-600" : vendor.risk_score < 50 ? "text-amber-600" : "text-red-600")}>
                        {vendor.risk_score}/100
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>

      {/* Vendor Detail */}
      {selectedVendor && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/30 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md h-full overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <h2 className="text-lg font-bold text-[#2a2017]">{selectedVendor.name}</h2>
              <button onClick={() => setSelectedVendor(null)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-5">
              <div className="rounded-xl bg-[#f9f6f1] border border-[#ede8e0] p-4 space-y-2">
                {[
                  ["Category", selectedVendor.category],
                  ["Contact", selectedVendor.contact],
                  ["Email", selectedVendor.email],
                  ["Phone", selectedVendor.phone],
                  ["Website", selectedVendor.website],
                  ["Payment Terms", selectedVendor.payment_terms],
                  ["YTD Spend", formatCurrency(selectedVendor.ytd_spend)],
                  ["Avg Days to Pay", `${selectedVendor.avg_days_to_pay} days`],
                  ["Invoices YTD", selectedVendor.invoices_ytd.toString()],
                  ["Last Payment", selectedVendor.last_payment],
                ].map(([label, value]) => (
                  <div key={label} className="flex justify-between text-sm">
                    <span className="text-[#776b5a]">{label}</span>
                    <span className="font-semibold text-[#2a2017]">{value}</span>
                  </div>
                ))}
              </div>
              <div className="rounded-xl border border-[#ede8e0] p-4">
                <p className="text-xs font-bold uppercase tracking-wide text-[#776b5a] mb-2">Risk Score</p>
                <div className="flex items-center gap-3">
                  <div className="flex-1 bg-[#f0ebe3] rounded-full h-3 overflow-hidden">
                    <div className={cn("h-full rounded-full", selectedVendor.risk_score < 25 ? "bg-emerald-500" : selectedVendor.risk_score < 50 ? "bg-amber-500" : "bg-red-500")} style={{ width: `${selectedVendor.risk_score}%` }} />
                  </div>
                  <span className={cn("text-lg font-black", selectedVendor.risk_score < 25 ? "text-emerald-600" : selectedVendor.risk_score < 50 ? "text-amber-600" : "text-red-600")}>{selectedVendor.risk_score}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <button className="rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea] flex items-center justify-center gap-2"><FileText className="h-4 w-4" /> View Bills</button>
                <button className="rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea] flex items-center justify-center gap-2"><Mail className="h-4 w-4" /> Contact</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showNewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <h2 className="text-lg font-bold text-[#2a2017]">Add Vendor</h2>
              <button onClick={() => setShowNewModal(false)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              {[["Vendor Name *", "Company name"], ["Contact Name", "Primary contact"], ["Email", "billing@vendor.com"], ["Phone", "+1-"], ["Website", "vendor.com"]].map(([label, placeholder]) => (
                <div key={label}>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">{label}</label>
                  <input placeholder={placeholder} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
                </div>
              ))}
              <div className="flex gap-3 pt-2">
                <button onClick={() => setShowNewModal(false)} className="flex-1 rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea]">Cancel</button>
                <button onClick={() => setShowNewModal(false)} className="flex-1 rounded-xl bg-[#231c15] py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">Add Vendor</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
