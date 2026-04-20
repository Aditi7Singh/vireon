"use client";

import { useState, useEffect } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import api from "@/lib/api";
import {
  Receipt, Plus, Search, Sparkles, CheckCircle2, Clock,
  AlertCircle, XCircle, Eye, X, ChevronRight,
  ThumbsUp, ThumbsDown, DollarSign, Calendar, Building2,
} from "lucide-react";

type BillStatus = "pending_approval" | "approved" | "scheduled" | "paid" | "overdue" | "rejected";

interface Bill {
  id: string;
  number: string;
  vendor: string;
  category: string;
  date: string;
  due_date: string;
  amount: number;
  status: BillStatus;
  po_number?: string;
  approver?: string;
  payment_method?: string;
}

const MOCK_BILLS: Bill[] = [
  { id: "1", number: "BILL-2026-087", vendor: "Amazon Web Services", category: "Infrastructure", date: "2026-04-01", due_date: "2026-04-30", amount: 14200, status: "approved", po_number: "PO-2026-012", approver: "Aditi Singh", payment_method: "ACH" },
  { id: "2", number: "BILL-2026-088", vendor: "Stripe Inc.", category: "Payment Processing", date: "2026-04-03", due_date: "2026-04-18", amount: 1840, status: "paid", approver: "Aditi Singh", payment_method: "ACH" },
  { id: "3", number: "BILL-2026-089", vendor: "Salesforce", category: "SaaS", date: "2026-04-05", due_date: "2026-05-05", amount: 8400, status: "pending_approval" },
  { id: "4", number: "BILL-2026-090", vendor: "Cooley LLP", category: "Legal", date: "2026-04-08", due_date: "2026-04-25", amount: 22500, status: "overdue" },
  { id: "5", number: "BILL-2026-091", vendor: "Greenhouse Software", category: "HR / ATS", date: "2026-04-10", due_date: "2026-05-10", amount: 3600, status: "pending_approval" },
  { id: "6", number: "BILL-2026-092", vendor: "WeWork", category: "Office Rent", date: "2026-04-12", due_date: "2026-04-12", amount: 9800, status: "paid", approver: "Aditi Singh", payment_method: "Wire" },
  { id: "7", number: "BILL-2026-093", vendor: "Datadog", category: "Monitoring", date: "2026-04-15", due_date: "2026-05-15", amount: 2100, status: "scheduled", approver: "Aditi Singh", payment_method: "ACH" },
  { id: "8", number: "BILL-2026-094", vendor: "Notion", category: "SaaS", date: "2026-04-18", due_date: "2026-05-18", amount: 480, status: "rejected" },
];

const statusMeta: Record<BillStatus, { label: string; color: string; bg: string; border: string; icon: React.ElementType }> = {
  pending_approval: { label: "Pending Approval", color: "#d97706", bg: "#fffbeb", border: "#fde68a", icon: Clock },
  approved:         { label: "Approved",         color: "#2563eb", bg: "#eff6ff", border: "#bfdbfe", icon: CheckCircle2 },
  scheduled:        { label: "Scheduled",        color: "#7c3aed", bg: "#f5f3ff", border: "#ddd6fe", icon: Calendar },
  paid:             { label: "Paid",             color: "#059669", bg: "#ecfdf5", border: "#a7f3d0", icon: CheckCircle2 },
  overdue:          { label: "Overdue",          color: "#dc2626", bg: "#fef2f2", border: "#fecaca", icon: AlertCircle },
  rejected:         { label: "Rejected",         color: "#6b7280", bg: "#f3f4f6", border: "#d1d5db", icon: XCircle },
};

const categoryColors: Record<string, string> = {
  "Infrastructure": "#2563eb", "SaaS": "#7c3aed", "Legal": "#dc2626",
  "HR / ATS": "#d97706", "Office Rent": "#059669", "Monitoring": "#0891b2",
  "Payment Processing": "#8b5cf6",
};

function mapBillStatus(s: string): BillStatus {
  const m: Record<string, BillStatus> = {
    PAID: "paid", OPEN: "approved", DRAFT: "pending_approval",
    OVERDUE: "overdue", PARTIALLY_PAID: "approved", SUBMITTED: "pending_approval", VOID: "rejected",
  };
  return m[s] ?? "approved";
}

export default function BillsPage() {
  const { openChat } = useAppStore();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<BillStatus | "all">("all");
  const [showNewModal, setShowNewModal] = useState(false);
  const [selectedBill, setSelectedBill] = useState<Bill | null>(null);
  const [bills, setBills] = useState<Bill[]>(MOCK_BILLS);
  const [newBill, setNewBill] = useState({ vendor: "", category: "SaaS", amount: "", due_date: "", description: "" });

  useEffect(() => {
    async function load() {
      try {
        const health = await api.getStartupHealth();
        const cid = health.default_company_id;
        if (!cid) return;
        const res = await api.getInvoicesList(cid, { type: "ACCOUNTS_PAYABLE" });
        if (res.invoices.length > 0) {
          setBills(res.invoices.map(inv => ({
            id: inv.id,
            number: inv.invoice_number,
            vendor: inv.contact_name || "Unknown Vendor",
            category: inv.memo?.split(" ")[0] || "SaaS",
            date: inv.issue_date,
            due_date: inv.due_date,
            amount: inv.total_amount,
            status: mapBillStatus(inv.status),
          })));
        }
      } catch {
        // keep mock data
      }
    }
    load();
  }, []);

  const filtered = bills.filter((b) => {
    const matchSearch = b.vendor.toLowerCase().includes(search.toLowerCase()) || b.number.includes(search);
    const matchStatus = statusFilter === "all" || b.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const stats = {
    total_due: bills.filter(b => ["approved", "scheduled", "overdue"].includes(b.status)).reduce((s, b) => s + b.amount, 0),
    pending: bills.filter(b => b.status === "pending_approval").reduce((s, b) => s + b.amount, 0),
    overdue: bills.filter(b => b.status === "overdue").reduce((s, b) => s + b.amount, 0),
    paid_mtd: bills.filter(b => b.status === "paid").reduce((s, b) => s + b.amount, 0),
  };

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Bills & Payables" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* Hero */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Receipt className="h-3.5 w-3.5" /> Accounts Payable
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Bills & AP Management</h1>
              <p className="mt-1 text-sm text-[#5f5344]">Track vendor bills, manage approvals, and schedule payments with AI-powered insights.</p>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => openChat("Analyze AP cash flow and suggest optimal payment timing")} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <Sparkles className="h-4 w-4" /> Optimize Cash
              </button>
              <button onClick={() => setShowNewModal(true)} className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                <Plus className="h-4 w-4" /> Enter Bill
              </button>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Bills Due (Apr)", value: formatCurrency(stats.total_due), color: "text-[#2a2017]" },
            { label: "Pending Approval", value: formatCurrency(stats.pending), color: "text-amber-700" },
            { label: "Overdue", value: formatCurrency(stats.overdue), color: "text-red-600" },
            { label: "Paid This Month", value: formatCurrency(stats.paid_mtd), color: "text-emerald-700" },
          ].map((s) => (
            <article key={s.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{s.label}</p>
              <p className={cn("mt-2 text-2xl font-bold", s.color)}>{s.value}</p>
            </article>
          ))}
        </section>

        {/* Pending Approvals Banner */}
        {bills.filter(b => b.status === "pending_approval").length > 0 && (
          <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Clock className="h-5 w-5 text-amber-600" />
                <div>
                  <p className="text-sm font-bold text-amber-900">{bills.filter(b => b.status === "pending_approval").length} bills awaiting your approval</p>
                  <p className="text-xs text-amber-700">Total pending: {formatCurrency(stats.pending)}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="rounded-lg bg-white border border-amber-300 px-3 py-1.5 text-xs font-semibold text-amber-800 hover:bg-amber-50 inline-flex items-center gap-1">
                  <ThumbsUp className="h-3.5 w-3.5" /> Approve All
                </button>
                <button className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-700 inline-flex items-center gap-1">
                  Review <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </section>
        )}

        {/* Filters + Table */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between border-b border-[#ede8e0]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9a8872]" />
              <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search bills..." className="rounded-xl border border-[#ddd2c2] bg-[#f9f6f1] py-2 pl-9 pr-4 text-sm w-64 outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {(["all", "pending_approval", "approved", "scheduled", "paid", "overdue", "rejected"] as const).map((s) => (
                <button key={s} onClick={() => setStatusFilter(s)} className={cn("rounded-full px-3 py-1 text-xs font-semibold border capitalize transition-all", statusFilter === s ? "bg-[#231c15] text-white border-[#231c15]" : "bg-white border-[#ddd2c2] text-[#776b5a] hover:border-[#b8a898]")}>
                  {s === "all" ? "All" : statusMeta[s as BillStatus].label}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#f9f5ef] text-[#776b5a]">
                <tr>
                  {["Bill #", "Vendor", "Category", "Date", "Due", "Amount", "Status", "Actions"].map((h) => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-bold uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0ebe3]">
                {filtered.map((bill) => {
                  const meta = statusMeta[bill.status];
                  const StatusIcon = meta.icon;
                  const catColor = categoryColors[bill.category] || "#8d4f27";
                  return (
                    <tr key={bill.id} className="hover:bg-[#fdf9f4] transition-colors">
                      <td className="px-5 py-4 font-mono text-xs font-semibold text-[#8d4f27]">{bill.number}</td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-lg bg-[#f0ebe3] flex items-center justify-center shrink-0">
                            <Building2 className="h-4 w-4 text-[#8d4f27]" />
                          </div>
                          <span className="font-semibold text-[#2a2017]">{bill.vendor}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="rounded-full px-2 py-0.5 text-xs font-semibold" style={{ background: `${catColor}15`, color: catColor }}>
                          {bill.category}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-[#5f5344]">{bill.date}</td>
                      <td className="px-5 py-4 text-[#5f5344]">{bill.due_date}</td>
                      <td className="px-5 py-4 font-semibold text-[#2a2017]">{formatCurrency(bill.amount)}</td>
                      <td className="px-5 py-4">
                        <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold border" style={{ color: meta.color, background: meta.bg, borderColor: meta.border }}>
                          <StatusIcon className="h-3 w-3" /> {meta.label}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-1">
                          {bill.status === "pending_approval" && (
                            <>
                              <button className="p-1.5 rounded-lg hover:bg-emerald-50 text-emerald-600" title="Approve"><ThumbsUp className="h-4 w-4" /></button>
                              <button className="p-1.5 rounded-lg hover:bg-red-50 text-red-500" title="Reject"><ThumbsDown className="h-4 w-4" /></button>
                            </>
                          )}
                          <button onClick={() => setSelectedBill(bill)} className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a]" title="View"><Eye className="h-4 w-4" /></button>
                          {bill.status === "approved" && (
                            <button className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a]" title="Schedule Payment"><DollarSign className="h-4 w-4" /></button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between px-5 py-3 border-t border-[#ede8e0] bg-[#faf7f3]">
            <p className="text-xs text-[#9a8872]">Showing {filtered.length} of {bills.length} bills</p>
          </div>
        </section>

        {/* AP Aging */}
        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5 sm:p-6">
            <h2 className="text-base font-bold text-[#2a2017] mb-4">AP Aging Summary</h2>
            <div className="space-y-3">
              {[
                { label: "Current (0–30 days)", amount: 28780, pct: 44, color: "bg-emerald-500" },
                { label: "31–60 days", amount: 22500, pct: 34, color: "bg-amber-500" },
                { label: "61–90 days", amount: 9800, pct: 15, color: "bg-orange-500" },
                { label: "90+ days", amount: 3600, pct: 7, color: "bg-red-500" },
              ].map((b) => (
                <div key={b.label} className="flex items-center gap-3">
                  <div className="w-32 text-xs text-[#776b5a] shrink-0">{b.label}</div>
                  <div className="flex-1 bg-[#f0ebe3] rounded-full h-2 overflow-hidden">
                    <div className={cn("h-full rounded-full", b.color)} style={{ width: `${b.pct}%` }} />
                  </div>
                  <div className="w-20 text-right text-sm font-semibold text-[#2a2017]">{formatCurrency(b.amount)}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5 sm:p-6">
            <h2 className="text-base font-bold text-[#2a2017] mb-4">Spend by Category</h2>
            <div className="space-y-3">
              {[
                { label: "Infrastructure", amount: 14200, color: "#2563eb" },
                { label: "Legal", amount: 22500, color: "#dc2626" },
                { label: "Office Rent", amount: 9800, color: "#059669" },
                { label: "SaaS Tools", amount: 8880, color: "#7c3aed" },
                { label: "HR / Hiring", amount: 3600, color: "#d97706" },
              ].map((c) => {
                const total = 58980;
                return (
                  <div key={c.label} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ background: c.color }} />
                      <span className="text-sm text-[#5f5344]">{c.label}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-24 bg-[#f0ebe3] rounded-full h-1.5 overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${(c.amount / total) * 100}%`, background: c.color }} />
                      </div>
                      <span className="text-sm font-semibold text-[#2a2017] w-20 text-right">{formatCurrency(c.amount)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      </div>

      {/* New Bill Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <h2 className="text-lg font-bold text-[#2a2017]">Enter Bill</h2>
              <button onClick={() => setShowNewModal(false)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              {[
                { label: "Vendor Name *", key: "vendor", placeholder: "Vendor Inc." },
                { label: "Description", key: "description", placeholder: "Service description" },
                { label: "Amount *", key: "amount", placeholder: "0.00", type: "number" },
                { label: "Due Date", key: "due_date", type: "date" },
              ].map(({ label, key, placeholder, type = "text" }) => (
                <div key={key}>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">{label}</label>
                  <input type={type} placeholder={placeholder} value={(newBill as any)[key]} onChange={(e) => setNewBill({ ...newBill, [key]: e.target.value })} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
                </div>
              ))}
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Category</label>
                <select value={newBill.category} onChange={(e) => setNewBill({ ...newBill, category: e.target.value })} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20">
                  {["SaaS", "Infrastructure", "Legal", "HR / ATS", "Office Rent", "Marketing", "Monitoring", "Other"].map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button onClick={() => setShowNewModal(false)} className="flex-1 rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea]">Cancel</button>
                <button className="flex-1 rounded-xl bg-[#231c15] py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">Submit for Approval</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bill Detail Drawer */}
      {selectedBill && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/30 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md h-full overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <div>
                <p className="text-xs text-[#9a8872] font-mono">{selectedBill.number}</p>
                <h2 className="text-lg font-bold text-[#2a2017]">{selectedBill.vendor}</h2>
              </div>
              <button onClick={() => setSelectedBill(null)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-6">
              {(() => { const meta = statusMeta[selectedBill.status]; const Icon = meta.icon; return (
                <span className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold border" style={{ color: meta.color, background: meta.bg, borderColor: meta.border }}>
                  <Icon className="h-4 w-4" /> {meta.label}
                </span>
              ); })()}
              <div className="rounded-xl bg-[#f9f6f1] border border-[#ede8e0] p-4 space-y-2">
                {[
                  ["Category", selectedBill.category],
                  ["Bill Date", selectedBill.date],
                  ["Due Date", selectedBill.due_date],
                  ["Amount", formatCurrency(selectedBill.amount)],
                  ...(selectedBill.po_number ? [["PO Number", selectedBill.po_number]] : []),
                  ...(selectedBill.approver ? [["Approved By", selectedBill.approver]] : []),
                  ...(selectedBill.payment_method ? [["Payment Method", selectedBill.payment_method]] : []),
                ].map(([label, value]) => (
                  <div key={label} className="flex justify-between text-sm">
                    <span className="text-[#776b5a]">{label}</span>
                    <span className="font-semibold text-[#2a2017]">{value}</span>
                  </div>
                ))}
              </div>
              {selectedBill.status === "pending_approval" && (
                <div className="grid grid-cols-2 gap-3">
                  <button className="rounded-xl bg-emerald-600 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 flex items-center justify-center gap-2">
                    <ThumbsUp className="h-4 w-4" /> Approve
                  </button>
                  <button className="rounded-xl bg-red-500 py-2.5 text-sm font-medium text-white hover:bg-red-600 flex items-center justify-center gap-2">
                    <ThumbsDown className="h-4 w-4" /> Reject
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
