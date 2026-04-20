"use client";

import { useState, useEffect } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import api from "@/lib/api";
import {
  UserCheck, Plus, Search, Sparkles, X, TrendingDown,
  AlertCircle, CheckCircle2, Mail, Star,
} from "lucide-react";

type CustomerHealth = "champion" | "healthy" | "at_risk" | "churned";

interface Customer {
  id: string;
  name: string;
  industry: string;
  plan: string;
  mrr: number;
  arr: number;
  since: string;
  renewal_date: string;
  health: CustomerHealth;
  nps: number;
  dso: number;
  owner: string;
  last_activity: string;
  seats: number;
  expansion_potential: number;
}

const CUSTOMERS: Customer[] = [
  { id: "1", name: "Meridian Bank", industry: "Financial Services", plan: "Enterprise", mrr: 12500, arr: 150000, since: "2024-01-15", renewal_date: "2027-01-15", health: "champion", nps: 72, dso: 14, owner: "Aditi Singh", last_activity: "2026-04-19", seats: 42, expansion_potential: 35000 },
  { id: "2", name: "Acme Corp", industry: "Manufacturing", plan: "Enterprise", mrr: 8200, arr: 98400, since: "2024-06-01", renewal_date: "2026-06-01", health: "healthy", nps: 58, dso: 28, owner: "Priya K.", last_activity: "2026-04-15", seats: 28, expansion_potential: 18000 },
  { id: "3", name: "Nexus Ventures", industry: "Finance / PE", plan: "Growth", mrr: 4800, arr: 57600, since: "2025-01-10", renewal_date: "2026-07-10", health: "at_risk", nps: 22, dso: 48, owner: "Aditi Singh", last_activity: "2026-03-28", seats: 12, expansion_potential: 0 },
  { id: "4", name: "Bloom Health", industry: "Healthcare", plan: "Growth", mrr: 3600, arr: 43200, since: "2025-03-01", renewal_date: "2026-09-01", health: "healthy", nps: 64, dso: 22, owner: "Rahul M.", last_activity: "2026-04-18", seats: 15, expansion_potential: 8000 },
  { id: "5", name: "Vertex Systems", industry: "Technology", plan: "Enterprise", mrr: 11000, arr: 132000, since: "2023-11-15", renewal_date: "2026-11-15", health: "champion", nps: 81, dso: 18, owner: "Priya K.", last_activity: "2026-04-20", seats: 65, expansion_potential: 42000 },
  { id: "6", name: "Skyline Retail", industry: "Retail", plan: "Starter", mrr: 1200, arr: 14400, since: "2025-07-01", renewal_date: "2026-07-01", health: "at_risk", nps: 15, dso: 62, owner: "Rahul M.", last_activity: "2026-03-10", seats: 4, expansion_potential: 0 },
  { id: "7", name: "Orion Logistics", industry: "Logistics", plan: "Growth", mrr: 3200, arr: 38400, since: "2025-02-01", renewal_date: "2026-08-01", health: "healthy", nps: 55, dso: 31, owner: "Aditi Singh", last_activity: "2026-04-17", seats: 18, expansion_potential: 6000 },
  { id: "8", name: "DeltaStream", industry: "Media", plan: "Starter", mrr: 800, arr: 9600, since: "2025-10-01", renewal_date: "2026-10-01", health: "churned", nps: -12, dso: 90, owner: "Priya K.", last_activity: "2026-02-01", seats: 3, expansion_potential: 0 },
];

const healthMeta: Record<CustomerHealth, { label: string; color: string; bg: string; border: string; icon: React.ElementType }> = {
  champion: { label: "Champion",  color: "#059669", bg: "#ecfdf5", border: "#a7f3d0", icon: Star },
  healthy:  { label: "Healthy",   color: "#2563eb", bg: "#eff6ff", border: "#bfdbfe", icon: CheckCircle2 },
  at_risk:  { label: "At Risk",   color: "#dc2626", bg: "#fef2f2", border: "#fecaca", icon: AlertCircle },
  churned:  { label: "Churned",   color: "#6b7280", bg: "#f3f4f6", border: "#d1d5db", icon: TrendingDown },
};

export default function CustomersPage() {
  const { openChat } = useAppStore();
  const [search, setSearch] = useState("");
  const [healthFilter, setHealthFilter] = useState<CustomerHealth | "all">("all");
  const [selected, setSelected] = useState<Customer | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [customers, setCustomers] = useState<Customer[]>(CUSTOMERS);

  useEffect(() => {
    async function load() {
      try {
        const health = await api.getStartupHealth();
        const cid = health.default_company_id;
        if (!cid) return;
        const res = await api.getContacts(cid, { type: "CUSTOMER" });
        if (res.contacts.length > 0) {
          setCustomers(res.contacts.map(c => ({
            id: c.id,
            name: c.name,
            industry: (c.billing_address as any)?.industry || "Technology",
            plan: (c.billing_address as any)?.plan || "Growth",
            mrr: (c.billing_address as any)?.mrr || 0,
            arr: (c.billing_address as any)?.arr || 0,
            since: c.created_at?.slice(0, 10) || "2025-01-01",
            renewal_date: (c.billing_address as any)?.renewal_date || "2026-12-31",
            health: (c.status === "active" ? "healthy" : "at_risk") as CustomerHealth,
            nps: (c.billing_address as any)?.nps || 50,
            dso: (c.billing_address as any)?.dso || 30,
            owner: "Aditi Singh",
            last_activity: c.created_at?.slice(0, 10) || "2026-04-01",
            seats: (c.billing_address as any)?.seats || 10,
            expansion_potential: (c.billing_address as any)?.expansion_potential || 0,
          })));
        }
      } catch {
        // keep mock data on error
      }
    }
    load();
  }, []);

  const filtered = customers.filter(c => {
    const matchSearch = c.name.toLowerCase().includes(search.toLowerCase()) || c.industry.toLowerCase().includes(search.toLowerCase());
    const matchHealth = healthFilter === "all" || c.health === healthFilter;
    return matchSearch && matchHealth;
  });

  const totalMRR = customers.filter(c => c.health !== "churned").reduce((s, c) => s + c.mrr, 0);
  const atRisk = customers.filter(c => c.health === "at_risk");
  const expansionPotential = customers.reduce((s, c) => s + c.expansion_potential, 0);
  const avgNPS = Math.round(customers.reduce((s, c) => s + c.nps, 0) / customers.length);

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Customers" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <UserCheck className="h-3.5 w-3.5" /> Customer Intelligence
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Customer Health & Revenue</h1>
              <p className="mt-1 text-sm text-[#5f5344]">Track account health, churn risk, NPS, and expansion opportunities.</p>
            </div>
            <div className="flex gap-3">
              <button onClick={() => openChat("Which customers are at churn risk and how should we save them?")} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <Sparkles className="h-4 w-4" /> Churn Analysis
              </button>
              <button onClick={() => setShowNew(true)} className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                <Plus className="h-4 w-4" /> Add Customer
              </button>
            </div>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Total MRR", value: formatCurrency(totalMRR), sub: `${CUSTOMERS.filter(c => c.health !== "churned").length} active accounts` },
            { label: "Expansion Potential", value: formatCurrency(expansionPotential), sub: "Upsell & cross-sell" },
            { label: "At Risk ARR", value: formatCurrency(atRisk.reduce((s, c) => s + c.arr, 0)), sub: `${atRisk.length} accounts`, color: "text-red-600" },
            { label: "Avg NPS", value: avgNPS.toString(), sub: avgNPS > 50 ? "World class" : avgNPS > 30 ? "Good" : "Needs work", color: avgNPS > 50 ? "text-emerald-700" : avgNPS > 30 ? "text-blue-700" : "text-red-600" },
          ].map((s) => (
            <article key={s.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{s.label}</p>
              <p className={cn("mt-2 text-2xl font-bold", s.color || "text-[#2a2017]")}>{s.value}</p>
              <p className="mt-1 text-xs text-[#9a8872]">{s.sub}</p>
            </article>
          ))}
        </section>

        {atRisk.length > 0 && (
          <section className="rounded-2xl border border-red-200 bg-red-50 p-4">
            <div className="flex items-center gap-3 mb-3">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <p className="text-sm font-bold text-red-900">{atRisk.length} accounts at churn risk — {formatCurrency(atRisk.reduce((s, c) => s + c.arr, 0))} ARR at stake</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {atRisk.map(c => (
                <button key={c.id} onClick={() => setSelected(c)} className="rounded-lg bg-white border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50">
                  {c.name} · NPS {c.nps}
                </button>
              ))}
            </div>
          </section>
        )}

        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between border-b border-[#ede8e0]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9a8872]" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search customers..." className="rounded-xl border border-[#ddd2c2] bg-[#f9f6f1] py-2 pl-9 pr-4 text-sm w-64 outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
            </div>
            <div className="flex gap-2 flex-wrap">
              {(["all", "champion", "healthy", "at_risk", "churned"] as const).map(h => (
                <button key={h} onClick={() => setHealthFilter(h)} className={cn("rounded-full px-3 py-1 text-xs font-semibold border capitalize transition-all", healthFilter === h ? "bg-[#231c15] text-white border-[#231c15]" : "bg-white border-[#ddd2c2] text-[#776b5a] hover:border-[#b8a898]")}>
                  {h === "all" ? "All" : healthMeta[h as CustomerHealth].label}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#f9f5ef] text-[#776b5a]">
                <tr>
                  {["Customer", "Plan", "MRR", "ARR", "NPS", "DSO", "Renewal", "Health", ""].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-bold uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0ebe3]">
                {filtered.map(c => {
                  const meta = healthMeta[c.health];
                  const Icon = meta.icon;
                  return (
                    <tr key={c.id} className="hover:bg-[#fdf9f4] transition-colors cursor-pointer" onClick={() => setSelected(c)}>
                      <td className="px-5 py-4">
                        <p className="font-semibold text-[#2a2017]">{c.name}</p>
                        <p className="text-xs text-[#9a8872]">{c.industry}</p>
                      </td>
                      <td className="px-5 py-4"><span className="text-xs font-semibold bg-[#f0ebe3] text-[#5f5344] px-2 py-0.5 rounded-full">{c.plan}</span></td>
                      <td className="px-5 py-4 font-semibold text-[#2a2017]">{formatCurrency(c.mrr)}</td>
                      <td className="px-5 py-4 text-[#5f5344]">{formatCurrency(c.arr)}</td>
                      <td className="px-5 py-4 font-bold" style={{ color: c.nps > 50 ? "#059669" : c.nps > 20 ? "#2563eb" : c.nps > 0 ? "#d97706" : "#dc2626" }}>{c.nps}</td>
                      <td className="px-5 py-4"><span className={cn("text-sm font-semibold", c.dso > 45 ? "text-red-600" : c.dso > 30 ? "text-amber-600" : "text-emerald-700")}>{c.dso}d</span></td>
                      <td className="px-5 py-4 text-[#5f5344]">{c.renewal_date}</td>
                      <td className="px-5 py-4">
                        <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold border" style={{ color: meta.color, background: meta.bg, borderColor: meta.border }}>
                          <Icon className="h-3 w-3" /> {meta.label}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        {c.expansion_potential > 0 && (
                          <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2 py-0.5">+{formatCurrency(c.expansion_potential)}</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/30 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md h-full overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <div>
                <h2 className="text-lg font-bold text-[#2a2017]">{selected.name}</h2>
                <p className="text-xs text-[#9a8872]">{selected.industry} · {selected.plan}</p>
              </div>
              <button onClick={() => setSelected(null)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-5">
              {(() => { const m = healthMeta[selected.health]; const I = m.icon; return (
                <span className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold border" style={{ color: m.color, background: m.bg, borderColor: m.border }}>
                  <I className="h-4 w-4" /> {m.label}
                </span>
              ); })()}
              <div className="grid grid-cols-2 gap-3">
                {[
                  ["MRR", formatCurrency(selected.mrr)],
                  ["ARR", formatCurrency(selected.arr)],
                  ["NPS Score", selected.nps.toString()],
                  ["DSO", `${selected.dso} days`],
                  ["Seats", selected.seats.toString()],
                  ["Customer Since", selected.since],
                  ["Renewal", selected.renewal_date],
                  ["Owner", selected.owner],
                ].map(([l, v]) => (
                  <div key={l} className="rounded-lg bg-[#f9f6f1] p-3">
                    <p className="text-xs text-[#776b5a]">{l}</p>
                    <p className="text-sm font-bold text-[#2a2017]">{v}</p>
                  </div>
                ))}
              </div>
              {selected.expansion_potential > 0 && (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                  <p className="text-xs font-bold text-emerald-800 uppercase tracking-wide">Expansion Opportunity</p>
                  <p className="text-2xl font-black text-emerald-700 mt-1">{formatCurrency(selected.expansion_potential)}</p>
                  <p className="text-xs text-emerald-600 mt-1">Upsell potential based on usage patterns</p>
                </div>
              )}
              <div className="grid grid-cols-2 gap-3">
                <button className="rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea] flex items-center justify-center gap-2"><Mail className="h-4 w-4" /> Email</button>
                <button onClick={() => { openChat(`What should I do about ${selected.name} — they are ${selected.health}`); setSelected(null); }} className="rounded-xl bg-[#231c15] py-2.5 text-sm font-medium text-white hover:bg-[#17120d] flex items-center justify-center gap-2"><Sparkles className="h-4 w-4" /> AI Playbook</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
