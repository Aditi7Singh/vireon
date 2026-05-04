"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import {
  Banknote, Plus, RefreshCw, ArrowLeftRight, CheckCircle2,
  AlertCircle, Clock, Upload, TrendingUp, TrendingDown,
  ChevronDown, X, Building2, CreditCard, DollarSign, Sparkles,
  Eye, Check, Link2,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Legend,
} from "recharts";

const BANK_ACCOUNTS = [
  {
    id: "1",
    name: "HDFC Current Account",
    bank: "HDFC Bank",
    number: "****4821",
    type: "checking",
    balance: 2840000,
    currency: "INR",
    lastSync: "2026-04-27 09:15",
    status: "synced",
    color: "#0066b2",
    transactions: 142,
    unreconciled: 8,
  },
  {
    id: "2",
    name: "ICICI Savings Account",
    bank: "ICICI Bank",
    number: "****9034",
    type: "savings",
    balance: 1250000,
    currency: "INR",
    lastSync: "2026-04-27 08:50",
    status: "synced",
    color: "#ff7700",
    transactions: 87,
    unreconciled: 3,
  },
  {
    id: "3",
    name: "Kotak Business Credit",
    bank: "Kotak Mahindra Bank",
    number: "****2277",
    type: "credit",
    balance: -380000,
    currency: "INR",
    lastSync: "2026-04-26 18:00",
    status: "pending",
    color: "#e11d48",
    transactions: 56,
    unreconciled: 12,
  },
  {
    id: "4",
    name: "USD Operating Account",
    bank: "Standard Chartered",
    number: "****5519",
    type: "checking",
    balance: 48000,
    currency: "USD",
    lastSync: "2026-04-27 07:30",
    status: "synced",
    color: "#0e7490",
    transactions: 23,
    unreconciled: 1,
  },
];

const RECENT_TRANSACTIONS = [
  { id: "1", date: "2026-04-27", description: "AWS Cloud Services - Monthly", amount: -48500, account: "HDFC Current", category: "Infrastructure", status: "matched", bankRef: "HDFC20260427001" },
  { id: "2", date: "2026-04-26", description: "Acme Corp - Invoice INV-2026-041", amount: 185000, account: "HDFC Current", category: "Revenue", status: "matched", bankRef: "HDFC20260426044" },
  { id: "3", date: "2026-04-26", description: "Office Rent - April 2026", amount: -125000, account: "HDFC Current", category: "Rent", status: "unmatched", bankRef: "HDFC20260426021" },
  { id: "4", date: "2026-04-25", description: "Salary Transfer - Engineering", amount: -840000, account: "HDFC Current", category: "Payroll", status: "matched", bankRef: "HDFC20260425103" },
  { id: "5", date: "2026-04-25", description: "Nexus Ventures - Partial Payment", amount: 72000, account: "ICICI Savings", category: "Revenue", status: "unmatched", bankRef: "ICICI20260425088" },
  { id: "6", date: "2026-04-24", description: "Zoom Pro - Annual", amount: -14999, account: "Kotak Credit", category: "Software", status: "matched", bankRef: "KTK20260424055" },
  { id: "7", date: "2026-04-24", description: "Google Workspace - 20 seats", amount: -18000, account: "Kotak Credit", category: "Software", status: "unmatched", bankRef: "KTK20260424056" },
  { id: "8", date: "2026-04-23", description: "Stripe payout - Week 17", amount: 143600, account: "USD Account", category: "Revenue", status: "matched", bankRef: "SC20260423017" },
];

const CASHFLOW_DATA = [
  { month: "Nov", inflow: 1240000, outflow: 980000 },
  { month: "Dec", inflow: 1580000, outflow: 1120000 },
  { month: "Jan", inflow: 1320000, outflow: 1050000 },
  { month: "Feb", inflow: 1680000, outflow: 1180000 },
  { month: "Mar", inflow: 1920000, outflow: 1340000 },
  { month: "Apr", inflow: 2100000, outflow: 1450000 },
];

const formatINR = (v: number) => {
  const abs = Math.abs(v);
  const sign = v < 0 ? "-" : "";
  if (abs >= 10_000_000) return `${sign}₹${(abs / 10_000_000).toFixed(1)}Cr`;
  if (abs >= 100_000) return `${sign}₹${(abs / 100_000).toFixed(1)}L`;
  if (abs >= 1_000) return `${sign}₹${(abs / 1_000).toFixed(1)}K`;
  return `${sign}₹${abs.toFixed(0)}`;
};

const ACCOUNT_TYPE_ICONS: Record<string, React.ElementType> = {
  checking: Banknote,
  savings: Building2,
  credit: CreditCard,
};

export default function BankingPage() {
  const { openChat } = useAppStore();
  const [activeTab, setActiveTab] = useState<"accounts" | "reconcile" | "feeds">("accounts");
  const [selectedAccountIds, setSelectedAccountIds] = useState<string[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [reconFilter, setReconFilter] = useState<"all" | "unmatched" | "matched">("all");

  useEffect(() => {
    const applyHash = () => {
      if (typeof window === "undefined") return;
      const hash = window.location.hash.toLowerCase();
      if (hash === "#reconcile") {
        setActiveTab("reconcile");
      } else if (hash === "#feeds") {
        setActiveTab("feeds");
      } else {
        setActiveTab("accounts");
      }
    };

    applyHash();
    window.addEventListener("hashchange", applyHash);
    return () => window.removeEventListener("hashchange", applyHash);
  }, []);

  const totalBalance = BANK_ACCOUNTS.reduce((s, a) => s + (a.currency === "INR" ? a.balance : a.balance * 83.5), 0);
  const totalUnreconciled = BANK_ACCOUNTS.reduce((s, a) => s + a.unreconciled, 0);

  const filteredTxns = RECENT_TRANSACTIONS.filter(t =>
    reconFilter === "all" ? true : t.status === reconFilter
  );

  const toggleSelectedAccount = (accountId: string) => {
    setSelectedAccountIds((current) =>
      current.includes(accountId)
        ? current.filter((id) => id !== accountId)
        : [...current, accountId]
    );
  };

  const TABS = [
    { id: "accounts", label: "Bank Accounts" },
    { id: "reconcile", label: `Reconciliation ${totalUnreconciled > 0 ? `(${totalUnreconciled})` : ""}` },
    { id: "feeds", label: "Bank Feeds" },
  ] as const;

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Banking" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* Hero */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Banknote className="h-3.5 w-3.5" /> Banking & Reconciliation
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Bank Accounts</h1>
              <p className="mt-1 text-sm text-[#5f5344]">Connect bank feeds, reconcile transactions, and monitor cash positions across all accounts.</p>
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              <button onClick={() => openChat("Analyze my bank account balances and flag any unusual transactions")} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <Sparkles className="h-4 w-4" /> AI Analyse
              </button>
              <button className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <Upload className="h-4 w-4" /> Import Statement
              </button>
              <button onClick={() => setShowAddModal(true)} className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                <Plus className="h-4 w-4" /> Connect Bank
              </button>
            </div>
          </div>
        </section>

        {/* Summary Stats */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Total Cash (INR equiv.)", value: formatINR(totalBalance), sub: `${BANK_ACCOUNTS.length} accounts`, color: "text-emerald-700", icon: DollarSign },
            { label: "Unreconciled Items", value: totalUnreconciled.toString(), sub: "Need attention", color: "text-amber-600", icon: AlertCircle },
            { label: "Apr Cash Inflow", value: formatINR(2100000), sub: "+9.4% vs Mar", color: "text-blue-700", icon: TrendingUp },
            { label: "Apr Cash Outflow", value: formatINR(1450000), sub: "+8.2% vs Mar", color: "text-red-600", icon: TrendingDown },
          ].map((s) => {
            const Icon = s.icon;
            return (
              <article key={s.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{s.label}</p>
                  <Icon className="h-4 w-4 text-[#87602a]" />
                </div>
                <p className={cn("text-2xl font-bold", s.color)}>{s.value}</p>
                <p className="mt-1 text-xs text-[#9a8872]">{s.sub}</p>
              </article>
            );
          })}
        </section>

        {/* Tabs */}
        <div className="flex gap-1 rounded-xl bg-[#f0e9e0] p-1 w-fit">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                if (typeof window !== "undefined") {
                  const targetHash = tab.id === "accounts" ? "" : `#${tab.id}`;
                  window.history.replaceState(null, "", `${window.location.pathname}${targetHash}`);
                }
              }}
              className={cn(
                "px-4 py-2 rounded-lg text-xs font-bold transition-all",
                activeTab === tab.id
                  ? "bg-white text-[#2a2017] shadow-sm"
                  : "text-[#776b5a] hover:text-[#2a2017]"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Accounts Tab */}
        {activeTab === "accounts" && (
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {BANK_ACCOUNTS.map((account) => {
                const TypeIcon = ACCOUNT_TYPE_ICONS[account.type] || Banknote;
                const isSelected = selectedAccountIds.includes(account.id);
                return (
                  <article
                    key={account.id}
                    onClick={() => toggleSelectedAccount(account.id)}
                    className={cn(
                      "rounded-2xl border p-5 cursor-pointer transition-all hover:shadow-md",
                      isSelected ? "border-[#b3622d] bg-[#fff8ec] shadow-md" : "border-[#ddd2c2] bg-[#fffdf8] hover:border-[#c4a882]"
                    )}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: account.color + "20" }}>
                          <TypeIcon className="h-4 w-4" style={{ color: account.color }} />
                        </div>
                        <div>
                          <p className="text-xs font-bold text-[#2a2017] leading-tight">{account.name}</p>
                          <p className="text-[10px] text-[#9a8872]">{account.bank}</p>
                        </div>
                      </div>
                      <span className={cn("text-[9px] font-black uppercase px-2 py-0.5 rounded-full",
                        account.status === "synced" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
                      )}>
                        {account.status === "synced" ? "Synced" : "Pending"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-[#9a8872]">
                      <span>{isSelected ? "Selected" : "Tap to select"}</span>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelectedAccount(account.id)}
                        onClick={(event) => event.stopPropagation()}
                        className="h-4 w-4 rounded border-[#c9b89f] text-[#8d4f27] focus:ring-[#8d4f27]"
                        aria-label={`Select ${account.name}`}
                      />
                    </div>
                    <p className={cn("text-2xl font-black", account.balance < 0 ? "text-red-600" : "text-[#2a2017]")}>
                      {account.currency === "USD" ? `$${(Math.abs(account.balance) / 1000).toFixed(0)}K` : formatINR(account.balance)}
                    </p>
                    <p className="text-xs text-[#9a8872] mt-1">{account.number} · {account.currency}</p>
                    <div className="mt-3 flex items-center justify-between text-[10px] text-[#9a8872]">
                      <span>{account.transactions} transactions</span>
                      {account.unreconciled > 0 && (
                        <span className="text-amber-600 font-bold">{account.unreconciled} unreconciled</span>
                      )}
                    </div>
                    <p className="text-[9px] text-[#b8a898] mt-1">Last sync: {account.lastSync}</p>
                  </article>
                );
              })}
            </div>

            {/* Cash Flow Chart */}
            <div className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-bold text-[#2a2017]">6-Month Cash Flow</h2>
                <span className="text-xs text-[#9a8872]">Nov 2025 – Apr 2026</span>
              </div>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={CASHFLOW_DATA} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0e8de" />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#776b5a" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: "#776b5a" }} axisLine={false} tickLine={false} tickFormatter={formatINR} />
                  <Tooltip
                    contentStyle={{ border: "1px solid #e3d6c7", borderRadius: 12, background: "#fffdf8", fontSize: 12 }}
                    formatter={(v: number) => [formatINR(v), ""]}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="inflow" name="Inflow" fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="outflow" name="Outflow" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Reconciliation Tab */}
        {activeTab === "reconcile" && (
          <div className="space-y-4">
            <div className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
              <div className="flex items-center justify-between p-5 border-b border-[#ede8e0]">
                <div>
                  <h2 className="text-base font-bold text-[#2a2017]">Transaction Matching</h2>
                  <p className="text-xs text-[#9a8872] mt-0.5">Match bank transactions to GL entries</p>
                </div>
                <div className="flex items-center gap-2">
                  {(["all", "unmatched", "matched"] as const).map((f) => (
                    <button key={f} onClick={() => setReconFilter(f)}
                      className={cn("px-3 py-1.5 rounded-lg text-xs font-semibold border capitalize transition-all",
                        reconFilter === f ? "bg-[#231c15] text-white border-[#231c15]" : "bg-white border-[#ddd2c2] text-[#776b5a] hover:border-[#b8a898]"
                      )}>
                      {f}
                    </button>
                  ))}
                </div>
              </div>

              <div className="divide-y divide-[#f0ebe3]">
                {filteredTxns.map((txn) => (
                  <div key={txn.id} className={cn("flex items-center gap-4 px-5 py-4 hover:bg-[#fdf9f4] transition-colors",
                    txn.status === "unmatched" && "bg-amber-50/40"
                  )}>
                    <div className={cn("w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                      txn.amount > 0 ? "bg-emerald-100" : "bg-red-100"
                    )}>
                      {txn.amount > 0 ? <TrendingUp className="h-4 w-4 text-emerald-600" /> : <TrendingDown className="h-4 w-4 text-red-500" />}
                    </div>

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-[#2a2017] truncate">{txn.description}</p>
                      <p className="text-xs text-[#9a8872]">{txn.date} · {txn.account} · Ref: {txn.bankRef}</p>
                    </div>

                    <div className="text-right shrink-0">
                      <p className={cn("text-sm font-bold", txn.amount > 0 ? "text-emerald-700" : "text-red-600")}>
                        {txn.amount > 0 ? "+" : ""}{formatINR(txn.amount)}
                      </p>
                      <p className="text-xs text-[#9a8872]">{txn.category}</p>
                    </div>

                    <div className="shrink-0">
                      {txn.status === "matched" ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-1 rounded-full">
                          <CheckCircle2 className="h-3 w-3" /> Matched
                        </span>
                      ) : (
                        <button className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-1 rounded-lg hover:bg-amber-100 transition-colors">
                          <Check className="h-3 w-3" /> Match
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between px-5 py-3 border-t border-[#ede8e0] bg-[#faf7f3]">
                <p className="text-xs text-[#9a8872]">
                  {filteredTxns.filter(t => t.status === "matched").length} matched · {filteredTxns.filter(t => t.status === "unmatched").length} unmatched
                </p>
                <button className="text-xs font-semibold text-[#8d4f27] hover:text-[#6b3a1e]">
                  Auto-match all →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Bank Feeds Tab */}
        {activeTab === "feeds" && (
          <div className="space-y-4">
            <div className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-6">
              <h2 className="text-base font-bold text-[#2a2017] mb-1">Connected Bank Feeds</h2>
              <p className="text-xs text-[#9a8872] mb-5">Automatic transaction import from your bank accounts</p>

              <div className="space-y-3">
                {BANK_ACCOUNTS.map((account) => {
                  const TypeIcon = ACCOUNT_TYPE_ICONS[account.type] || Banknote;
                  const isSelected = selectedAccountIds.includes(account.id);
                  return (
                    <div key={account.id} className="flex items-center gap-4 p-4 rounded-xl border border-[#ede8e0] bg-white">
                      <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0" style={{ background: account.color + "15" }}>
                        <TypeIcon className="h-5 w-5" style={{ color: account.color }} />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-[#2a2017]">{account.name}</p>
                        <p className="text-xs text-[#9a8872]">{account.bank} · {account.number}</p>
                      </div>
                      <div className="text-right text-xs text-[#9a8872]">
                        <p>Last import</p>
                        <p className="font-semibold text-[#2a2017]">{account.lastSync}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={cn("text-[10px] font-black uppercase px-2 py-1 rounded-full",
                          account.status === "synced" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
                        )}>
                          {account.status === "synced" ? "● Active" : "⚠ Pending"}
                        </span>
                        <label className="inline-flex items-center gap-2 rounded-lg border border-[#ddd2c2] px-2 py-1 text-[10px] font-semibold text-[#776b5a]">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSelectedAccount(account.id)}
                            className="h-3.5 w-3.5 rounded border-[#c9b89f] text-[#8d4f27] focus:ring-[#8d4f27]"
                            aria-label={`Connect ${account.name}`}
                          />
                          Selected
                        </label>
                        <button className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a]">
                          <RefreshCw className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-5 rounded-xl border-2 border-dashed border-[#d4c3ae] p-6 text-center">
                <Link2 className="h-8 w-8 text-[#9a8872] mx-auto mb-2" />
                <p className="text-sm font-semibold text-[#2a2017]">Connect another bank</p>
                <p className="text-xs text-[#9a8872] mt-1">Supports HDFC, ICICI, Axis, SBI, Kotak, and 40+ Indian banks</p>
                <button onClick={() => setShowAddModal(true)} className="mt-3 inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                  <Plus className="h-4 w-4" /> Add Bank Connection
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add Bank Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <h2 className="text-lg font-bold text-[#2a2017]">Connect Bank Account</h2>
              <button onClick={() => setShowAddModal(false)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Bank</label>
                <select className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none">
                  <option>HDFC Bank</option>
                  <option>ICICI Bank</option>
                  <option>Axis Bank</option>
                  <option>State Bank of India</option>
                  <option>Kotak Mahindra Bank</option>
                  <option>Yes Bank</option>
                  <option>IndusInd Bank</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Account Type</label>
                <select className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none">
                  <option>Current Account</option>
                  <option>Savings Account</option>
                  <option>Credit Card</option>
                  <option>Overdraft</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Account Number (last 4 digits)</label>
                <input className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none" placeholder="e.g. 4821" maxLength={4} />
              </div>
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Opening Balance (₹)</label>
                <input type="number" className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none" placeholder="0.00" />
              </div>
              <div className="rounded-xl bg-blue-50 border border-blue-200 p-3 text-xs text-blue-700">
                <strong>Demo mode:</strong> In production, this connects via secure bank API (netbanking / OFX feed). You can also upload bank statements manually.
              </div>
              <div className="flex gap-3 pt-2">
                <button onClick={() => setShowAddModal(false)} className="flex-1 rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea]">Cancel</button>
                <button onClick={() => setShowAddModal(false)} className="flex-1 rounded-xl bg-[#231c15] py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">Connect Account</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
