"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import {
  Scale, Plus, Search, Sparkles, ChevronRight, ChevronDown,
  X, BookOpen, DollarSign, TrendingUp, TrendingDown, Building2,
  FileText,
} from "lucide-react";

type AccountType = "asset" | "liability" | "equity" | "revenue" | "expense";

interface Account {
  id: string;
  code: string;
  name: string;
  type: AccountType;
  subtype: string;
  balance: number;
  normal_balance: "debit" | "credit";
  is_parent: boolean;
  parent_id?: string;
  description?: string;
}

const ACCOUNTS: Account[] = [
  // Assets
  { id: "1000", code: "1000", name: "Current Assets", type: "asset", subtype: "Current", balance: 3667000, normal_balance: "debit", is_parent: true },
  { id: "1010", code: "1010", name: "Cash & Cash Equivalents", type: "asset", subtype: "Current", balance: 2840000, normal_balance: "debit", is_parent: false, parent_id: "1000", description: "Operating bank accounts and money market" },
  { id: "1020", code: "1020", name: "Accounts Receivable", type: "asset", subtype: "Current", balance: 285000, normal_balance: "debit", is_parent: false, parent_id: "1000" },
  { id: "1030", code: "1030", name: "Prepaid Expenses", type: "asset", subtype: "Current", balance: 42000, normal_balance: "debit", is_parent: false, parent_id: "1000" },
  { id: "1040", code: "1040", name: "Short-Term Investments", type: "asset", subtype: "Current", balance: 500000, normal_balance: "debit", is_parent: false, parent_id: "1000" },
  { id: "1500", code: "1500", name: "Non-Current Assets", type: "asset", subtype: "Non-Current", balance: 220000, normal_balance: "debit", is_parent: true },
  { id: "1510", code: "1510", name: "Fixed Assets (Gross)", type: "asset", subtype: "Fixed", balance: 180000, normal_balance: "debit", is_parent: false, parent_id: "1500" },
  { id: "1520", code: "1520", name: "Accumulated Depreciation", type: "asset", subtype: "Fixed", balance: -56000, normal_balance: "credit", is_parent: false, parent_id: "1500" },
  { id: "1530", code: "1530", name: "Intangible Assets (Net)", type: "asset", subtype: "Intangible", balance: 68000, normal_balance: "debit", is_parent: false, parent_id: "1500" },
  // Liabilities
  { id: "2000", code: "2000", name: "Current Liabilities", type: "liability", subtype: "Current", balance: 314800, normal_balance: "credit", is_parent: true },
  { id: "2010", code: "2010", name: "Accounts Payable", type: "liability", subtype: "Current", balance: 64800, normal_balance: "credit", is_parent: false, parent_id: "2000" },
  { id: "2020", code: "2020", name: "Accrued Expenses", type: "liability", subtype: "Current", balance: 38000, normal_balance: "credit", is_parent: false, parent_id: "2000" },
  { id: "2030", code: "2030", name: "Deferred Revenue", type: "liability", subtype: "Current", balance: 212000, normal_balance: "credit", is_parent: false, parent_id: "2000" },
  { id: "2500", code: "2500", name: "Non-Current Liabilities", type: "liability", subtype: "Non-Current", balance: 18000, normal_balance: "credit", is_parent: true },
  { id: "2510", code: "2510", name: "Deferred Tax Liability", type: "liability", subtype: "Non-Current", balance: 18000, normal_balance: "credit", is_parent: false, parent_id: "2500" },
  // Equity
  { id: "3000", code: "3000", name: "Shareholders' Equity", type: "equity", subtype: "Equity", balance: 3554200, normal_balance: "credit", is_parent: true },
  { id: "3010", code: "3010", name: "Common Stock & APIC", type: "equity", subtype: "Stock", balance: 2980000, normal_balance: "credit", is_parent: false, parent_id: "3000" },
  { id: "3020", code: "3020", name: "Retained Earnings", type: "equity", subtype: "Earnings", balance: 574200, normal_balance: "credit", is_parent: false, parent_id: "3000" },
  // Revenue
  { id: "4000", code: "4000", name: "Revenue", type: "revenue", subtype: "Operating", balance: 485000, normal_balance: "credit", is_parent: true },
  { id: "4010", code: "4010", name: "SaaS Subscription Revenue", type: "revenue", subtype: "Recurring", balance: 385000, normal_balance: "credit", is_parent: false, parent_id: "4000" },
  { id: "4020", code: "4020", name: "Professional Services Revenue", type: "revenue", subtype: "Non-Recurring", balance: 72000, normal_balance: "credit", is_parent: false, parent_id: "4000" },
  { id: "4030", code: "4030", name: "Implementation Revenue", type: "revenue", subtype: "Non-Recurring", balance: 28000, normal_balance: "credit", is_parent: false, parent_id: "4000" },
  // Expenses
  { id: "5000", code: "5000", name: "Cost of Revenue", type: "expense", subtype: "COGS", balance: 104600, normal_balance: "debit", is_parent: true },
  { id: "5010", code: "5010", name: "Hosting & Infrastructure", type: "expense", subtype: "COGS", balance: 54200, normal_balance: "debit", is_parent: false, parent_id: "5000" },
  { id: "5020", code: "5020", name: "Support Staff", type: "expense", subtype: "COGS", balance: 38000, normal_balance: "debit", is_parent: false, parent_id: "5000" },
  { id: "5030", code: "5030", name: "Third-Party APIs", type: "expense", subtype: "COGS", balance: 12400, normal_balance: "debit", is_parent: false, parent_id: "5000" },
  { id: "6000", code: "6000", name: "Operating Expenses", type: "expense", subtype: "OpEx", balance: 376700, normal_balance: "debit", is_parent: true },
  { id: "6010", code: "6010", name: "Salaries & Benefits", type: "expense", subtype: "Personnel", balance: 186000, normal_balance: "debit", is_parent: false, parent_id: "6000" },
  { id: "6020", code: "6020", name: "Sales & Marketing", type: "expense", subtype: "GTM", balance: 68000, normal_balance: "debit", is_parent: false, parent_id: "6000" },
  { id: "6030", code: "6030", name: "Research & Development", type: "expense", subtype: "R&D", balance: 52000, normal_balance: "debit", is_parent: false, parent_id: "6000" },
  { id: "6040", code: "6040", name: "General & Administrative", type: "expense", subtype: "G&A", balance: 34000, normal_balance: "debit", is_parent: false, parent_id: "6000" },
  { id: "6050", code: "6050", name: "Legal & Compliance", type: "expense", subtype: "G&A", balance: 22500, normal_balance: "debit", is_parent: false, parent_id: "6000" },
  { id: "6060", code: "6060", name: "Office & Facilities", type: "expense", subtype: "G&A", balance: 14200, normal_balance: "debit", is_parent: false, parent_id: "6000" },
];

const typeConfig: Record<AccountType, { label: string; color: string; bg: string; icon: React.ElementType }> = {
  asset:     { label: "Asset",     color: "#2563eb", bg: "#eff6ff", icon: Building2 },
  liability: { label: "Liability", color: "#dc2626", bg: "#fef2f2", icon: TrendingDown },
  equity:    { label: "Equity",    color: "#7c3aed", bg: "#f5f3ff", icon: DollarSign },
  revenue:   { label: "Revenue",   color: "#059669", bg: "#ecfdf5", icon: TrendingUp },
  expense:   { label: "Expense",   color: "#d97706", bg: "#fffbeb", icon: TrendingDown },
};

interface JournalLine {
  account: string;
  description: string;
  debit: number;
  credit: number;
}

export default function ChartOfAccountsPage() {
  const { openChat } = useAppStore();
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<AccountType | "all">("all");
  const [expanded, setExpanded] = useState<Set<string>>(new Set(["1000", "2000", "3000", "4000", "5000", "6000"]));
  const [showJEModal, setShowJEModal] = useState(false);
  const [showNewAcctModal, setShowNewAcctModal] = useState(false);
  const [journalDate, setJournalDate] = useState("2026-04-20");
  const [journalMemo, setJournalMemo] = useState("");
  const [journalLines, setJournalLines] = useState<JournalLine[]>([
    { account: "", description: "", debit: 0, credit: 0 },
    { account: "", description: "", debit: 0, credit: 0 },
  ]);

  const toggleExpand = (id: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const filteredParents = ACCOUNTS.filter(a => a.is_parent && (typeFilter === "all" || a.type === typeFilter));
  const getChildren = (parentId: string) => ACCOUNTS.filter(a => !a.is_parent && a.parent_id === parentId && (search === "" || a.name.toLowerCase().includes(search.toLowerCase()) || a.code.includes(search)));

  const totalDebits = journalLines.reduce((s, l) => s + l.debit, 0);
  const totalCredits = journalLines.reduce((s, l) => s + l.credit, 0);
  const isBalanced = Math.abs(totalDebits - totalCredits) < 0.01;

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Chart of Accounts" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Scale className="h-3.5 w-3.5" /> Double-Entry Accounting
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Chart of Accounts</h1>
              <p className="mt-1 text-sm text-[#5f5344]">Manage your general ledger account structure and create journal entries.</p>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => setShowJEModal(true)} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <FileText className="h-4 w-4" /> Journal Entry
              </button>
              <button onClick={() => setShowNewAcctModal(true)} className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                <Plus className="h-4 w-4" /> Add Account
              </button>
            </div>
          </div>
        </section>

        {/* Summary Tiles */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {(["asset", "liability", "equity", "revenue", "expense"] as AccountType[]).map(type => {
            const cfg = typeConfig[type];
            const Icon = cfg.icon;
            const total = ACCOUNTS.filter(a => a.type === type && !a.is_parent).reduce((s, a) => s + a.balance, 0);
            return (
              <button key={type} onClick={() => setTypeFilter(typeFilter === type ? "all" : type)} className={cn("rounded-2xl border p-4 text-left transition-all", typeFilter === type ? "ring-2 ring-offset-1" : "hover:shadow-md")} style={{ background: cfg.bg, borderColor: typeFilter === type ? cfg.color : "#ede8e0" }}>
                <div className="flex items-center gap-2 mb-2">
                  <Icon className="h-4 w-4" style={{ color: cfg.color }} />
                  <p className="text-xs font-bold uppercase tracking-wide" style={{ color: cfg.color }}>{cfg.label}</p>
                </div>
                <p className="text-xl font-black" style={{ color: cfg.color }}>{formatCurrency(Math.abs(total))}</p>
                <p className="text-xs mt-1" style={{ color: cfg.color, opacity: 0.7 }}>{ACCOUNTS.filter(a => a.type === type && !a.is_parent).length} accounts</p>
              </button>
            );
          })}
        </section>

        {/* Filters + Table */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="flex items-center gap-3 p-5 border-b border-[#ede8e0]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9a8872]" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search accounts..." className="rounded-xl border border-[#ddd2c2] bg-[#f9f6f1] py-2 pl-9 pr-4 text-sm w-64 outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#f9f5ef]">
                <tr>
                  {["Code", "Account Name", "Type", "Normal Bal.", "Balance", ""].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-bold uppercase tracking-wide text-[#776b5a]">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredParents.map(parent => {
                  const cfg = typeConfig[parent.type];
                  const children = getChildren(parent.id);
                  const isOpen = expanded.has(parent.id);
                  if (children.length === 0 && search !== "") return null;
                  return (
                    <>
                      <tr key={parent.id} className="bg-[#f5f0ea] cursor-pointer hover:bg-[#ede8e0] transition-colors" onClick={() => toggleExpand(parent.id)}>
                        <td className="px-5 py-3 font-mono text-xs font-bold text-[#6b5344]">{parent.code}</td>
                        <td className="px-5 py-3 font-black text-[#2a2017] flex items-center gap-2">
                          {isOpen ? <ChevronDown className="h-3.5 w-3.5 text-[#8d4f27]" /> : <ChevronRight className="h-3.5 w-3.5 text-[#8d4f27]" />}
                          {parent.name}
                        </td>
                        <td className="px-5 py-3">
                          <span className="rounded-full px-2 py-0.5 text-xs font-bold" style={{ background: cfg.bg, color: cfg.color }}>{cfg.label}</span>
                        </td>
                        <td className="px-5 py-3 text-xs text-[#776b5a] capitalize">{parent.normal_balance}</td>
                        <td className="px-5 py-3 font-bold text-[#2a2017]">{formatCurrency(Math.abs(parent.balance))}</td>
                        <td className="px-5 py-3" />
                      </tr>
                      {isOpen && children.map(acct => (
                        <tr key={acct.id} className="border-b border-[#f5f0ea] hover:bg-[#fdf9f4] transition-colors">
                          <td className="px-5 py-2.5 font-mono text-xs text-[#9a8872] pl-10">{acct.code}</td>
                          <td className="px-5 py-2.5 pl-12 text-[#4a3f35]">{acct.name}</td>
                          <td className="px-5 py-2.5 text-xs text-[#9a8872]">{acct.subtype}</td>
                          <td className="px-5 py-2.5 text-xs text-[#9a8872] capitalize">{acct.normal_balance}</td>
                          <td className="px-5 py-2.5 font-semibold text-[#2a2017]">{formatCurrency(Math.abs(acct.balance))}</td>
                          <td className="px-5 py-2.5">
                            <button className="text-xs text-[#8d4f27] hover:underline">View GL</button>
                          </td>
                        </tr>
                      ))}
                    </>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      {/* Journal Entry Modal */}
      {showJEModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <h2 className="text-lg font-bold text-[#2a2017]">Manual Journal Entry</h2>
              <button onClick={() => setShowJEModal(false)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Date</label>
                  <input type="date" value={journalDate} onChange={e => setJournalDate(e.target.value)} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Memo</label>
                  <input value={journalMemo} onChange={e => setJournalMemo(e.target.value)} placeholder="Entry description" className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
                </div>
              </div>

              <div className="rounded-xl border border-[#ddd2c2] overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-[#f9f5ef]">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-bold text-[#776b5a]">Account</th>
                      <th className="px-4 py-2 text-left text-xs font-bold text-[#776b5a]">Description</th>
                      <th className="px-4 py-2 text-right text-xs font-bold text-[#776b5a]">Debit</th>
                      <th className="px-4 py-2 text-right text-xs font-bold text-[#776b5a]">Credit</th>
                      <th className="px-2 py-2" />
                    </tr>
                  </thead>
                  <tbody>
                    {journalLines.map((line, i) => (
                      <tr key={i} className="border-t border-[#f0ebe3]">
                        <td className="px-4 py-2">
                          <select value={line.account} onChange={e => { const l = [...journalLines]; l[i].account = e.target.value; setJournalLines(l); }} className="w-full bg-transparent text-sm outline-none">
                            <option value="">Select account</option>
                            {ACCOUNTS.filter(a => !a.is_parent).map(a => <option key={a.id} value={a.code}>{a.code} — {a.name}</option>)}
                          </select>
                        </td>
                        <td className="px-4 py-2"><input value={line.description} onChange={e => { const l = [...journalLines]; l[i].description = e.target.value; setJournalLines(l); }} className="w-full bg-transparent text-sm outline-none" placeholder="Line memo" /></td>
                        <td className="px-4 py-2"><input type="number" value={line.debit || ""} onChange={e => { const l = [...journalLines]; l[i].debit = Number(e.target.value); l[i].credit = 0; setJournalLines(l); }} className="w-24 bg-transparent text-right text-sm outline-none" placeholder="0.00" /></td>
                        <td className="px-4 py-2"><input type="number" value={line.credit || ""} onChange={e => { const l = [...journalLines]; l[i].credit = Number(e.target.value); l[i].debit = 0; setJournalLines(l); }} className="w-24 bg-transparent text-right text-sm outline-none" placeholder="0.00" /></td>
                        <td className="px-2 py-2"><button onClick={() => setJournalLines(journalLines.filter((_, j) => j !== i))} className="text-[#c0392b]"><X className="h-4 w-4" /></button></td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-[#f9f5ef]">
                    <tr>
                      <td colSpan={2} className="px-4 py-2 text-xs font-bold text-[#776b5a]">TOTAL</td>
                      <td className="px-4 py-2 text-right font-bold text-[#2a2017]">{formatCurrency(totalDebits)}</td>
                      <td className="px-4 py-2 text-right font-bold text-[#2a2017]">{formatCurrency(totalCredits)}</td>
                      <td />
                    </tr>
                  </tfoot>
                </table>
              </div>

              <button onClick={() => setJournalLines([...journalLines, { account: "", description: "", debit: 0, credit: 0 }])} className="text-xs font-semibold text-[#8d4f27] flex items-center gap-1">
                <Plus className="h-3.5 w-3.5" /> Add Line
              </button>

              {!isBalanced && totalDebits > 0 && (
                <p className="text-xs text-red-600 font-semibold">⚠ Entry is out of balance by {formatCurrency(Math.abs(totalDebits - totalCredits))}</p>
              )}

              <div className="flex gap-3 pt-2">
                <button onClick={() => setShowJEModal(false)} className="flex-1 rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea]">Cancel</button>
                <button disabled={!isBalanced || totalDebits === 0} className="flex-1 rounded-xl bg-[#231c15] py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d] disabled:opacity-50">Post Journal Entry</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showNewAcctModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <h2 className="text-lg font-bold text-[#2a2017]">New Account</h2>
              <button onClick={() => setShowNewAcctModal(false)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              {[["Account Code", "e.g. 4040"], ["Account Name", "e.g. Consulting Revenue"]].map(([label, placeholder]) => (
                <div key={label}>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">{label}</label>
                  <input placeholder={placeholder} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
                </div>
              ))}
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Account Type</label>
                <select className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20">
                  {["Asset", "Liability", "Equity", "Revenue", "Expense"].map(t => <option key={t}>{t}</option>)}
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button onClick={() => setShowNewAcctModal(false)} className="flex-1 rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea]">Cancel</button>
                <button onClick={() => setShowNewAcctModal(false)} className="flex-1 rounded-xl bg-[#231c15] py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">Create Account</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
