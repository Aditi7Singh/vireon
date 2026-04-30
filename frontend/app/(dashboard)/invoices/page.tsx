"use client";

import { useState, useEffect } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import api from "@/lib/api";
import {
  FileText, Plus, Send, Download, Search, Sparkles,
  CheckCircle2, Clock, AlertCircle, Eye, MoreHorizontal,
  Mail, Copy, X, DollarSign,
} from "lucide-react";

type InvoiceStatus = "draft" | "sent" | "viewed" | "partial" | "paid" | "overdue";

interface Invoice {
  id: string;
  number: string;
  customer: string;
  email: string;
  date: string;
  due_date: string;
  amount: number;
  paid: number;
  status: InvoiceStatus;
  items: { description: string; qty: number; rate: number }[];
}

const MOCK_INVOICES: Invoice[] = [
  { id: "1", number: "INV-2026-041", customer: "Acme Corp", email: "ap@acmecorp.com", date: "2026-04-01", due_date: "2026-05-01", amount: 18500, paid: 18500, status: "paid", items: [{ description: "Analytics Platform — Enterprise License Q2", qty: 1, rate: 18500 }] },
  { id: "2", number: "INV-2026-042", customer: "Nexus Ventures", email: "finance@nexusvc.com", date: "2026-04-05", due_date: "2026-05-05", amount: 7200, paid: 0, status: "overdue", items: [{ description: "Professional Services — April", qty: 24, rate: 300 }] },
  { id: "3", number: "INV-2026-043", customer: "Bloom Health", email: "billing@bloomhealth.io", date: "2026-04-10", due_date: "2026-05-10", amount: 4800, paid: 0, status: "sent", items: [{ description: "SaaS Subscription — Growth Plan", qty: 4, rate: 1200 }] },
  { id: "4", number: "INV-2026-044", customer: "Vertex Systems", email: "accounts@vertexsys.com", date: "2026-04-12", due_date: "2026-05-12", amount: 22000, paid: 11000, status: "partial", items: [{ description: "Implementation Services Phase 2", qty: 1, rate: 22000 }] },
  { id: "5", number: "INV-2026-045", customer: "Skyline Retail", email: "ap@skylineretail.com", date: "2026-04-15", due_date: "2026-05-15", amount: 3600, paid: 0, status: "viewed", items: [{ description: "Monthly Reporting Module — May", qty: 1, rate: 3600 }] },
  { id: "6", number: "INV-2026-046", customer: "Meridian Bank", email: "vendors@meridianbank.com", date: "2026-04-18", due_date: "2026-05-18", amount: 41000, paid: 0, status: "sent", items: [{ description: "Enterprise Analytics — Annual Renewal", qty: 1, rate: 41000 }] },
  { id: "7", number: "INV-2026-047", customer: "Orion Logistics", email: "finance@orionlog.com", date: "2026-04-20", due_date: "2026-04-20", amount: 2100, paid: 0, status: "draft", items: [{ description: "Custom Dashboard Development", qty: 7, rate: 300 }] },
];

const statusMeta: Record<InvoiceStatus, { label: string; color: string; bg: string; border: string; icon: React.ElementType }> = {
  draft:   { label: "Draft",   color: "#6b7280", bg: "#f3f4f6", border: "#d1d5db", icon: FileText },
  sent:    { label: "Sent",    color: "#2563eb", bg: "#eff6ff", border: "#bfdbfe", icon: Send },
  viewed:  { label: "Viewed",  color: "#7c3aed", bg: "#f5f3ff", border: "#ddd6fe", icon: Eye },
  partial: { label: "Partial", color: "#d97706", bg: "#fffbeb", border: "#fde68a", icon: Clock },
  paid:    { label: "Paid",    color: "#059669", bg: "#ecfdf5", border: "#a7f3d0", icon: CheckCircle2 },
  overdue: { label: "Overdue", color: "#dc2626", bg: "#fef2f2", border: "#fecaca", icon: AlertCircle },
};

function mapStatus(s: string): InvoiceStatus {
  const m: Record<string, InvoiceStatus> = {
    PAID: "paid", OPEN: "sent", DRAFT: "draft",
    OVERDUE: "overdue", PARTIALLY_PAID: "partial", SUBMITTED: "viewed", VOID: "draft",
  };
  return m[s] ?? "sent";
}

function exportCSV(invoices: Invoice[]) {
  const header = ["Invoice #", "Customer", "Email", "Date", "Due Date", "Amount", "Paid", "Balance Due", "Status"];
  const rows = invoices.map((inv) => [
    inv.number, inv.customer, inv.email, inv.date, inv.due_date,
    inv.amount, inv.paid, inv.amount - inv.paid, inv.status,
  ]);
  const csv = [header, ...rows].map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `invoices-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function InvoicesPage() {
  const { openChat } = useAppStore();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<InvoiceStatus | "all">("all");
  const [showNewModal, setShowNewModal] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>(MOCK_INVOICES);
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);
  const [savingInvoice, setSavingInvoice] = useState(false);

  // Payment modal state
  const [paymentModal, setPaymentModal] = useState<{ invoice: Invoice; amount: string; date: string } | null>(null);
  const [recordingPayment, setRecordingPayment] = useState(false);

  const [newInvoice, setNewInvoice] = useState({
    customer: "", email: "", due_date: "", items: [{ description: "", qty: 1, rate: 0 }],
  });

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3500);
  };

  useEffect(() => {
    async function load() {
      try {
        const health = await api.getStartupHealth();
        const cid = health.default_company_id;
        if (!cid) return;
        setCompanyId(cid);
        const res = await api.getInvoicesList(cid, { type: "ACCOUNTS_RECEIVABLE" });
        if (res.invoices.length > 0) {
          setInvoices(res.invoices.map((inv: any) => ({
            id: inv.id,
            number: inv.invoice_number,
            customer: inv.contact_name || "Unknown",
            email: "",
            date: inv.issue_date,
            due_date: inv.due_date,
            amount: inv.total_amount,
            paid: inv.amount_paid,
            status: mapStatus(inv.status),
            items: [{ description: inv.memo || "Service", qty: 1, rate: inv.total_amount }],
          })));
        }
      } catch {
        // keep mock data
      }
    }
    load();
  }, []);

  const filtered = invoices.filter((inv) => {
    const matchSearch = inv.customer.toLowerCase().includes(search.toLowerCase()) || inv.number.includes(search);
    const matchStatus = statusFilter === "all" || inv.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const outstandingInvs = invoices.filter((i) => ["sent", "viewed", "partial"].includes(i.status));
  const overdueInvs     = invoices.filter((i) => i.status === "overdue");
  const paidInvs        = invoices.filter((i) => i.status === "paid");

  const stats = {
    total:       invoices.reduce((s, i) => s + i.amount, 0),
    totalCount:  invoices.length,
    outstanding: outstandingInvs.reduce((s, i) => s + (i.amount - i.paid), 0),
    outstandingCount: outstandingInvs.length,
    overdue:     overdueInvs.reduce((s, i) => s + i.amount, 0),
    overdueCount: overdueInvs.length,
    paid_mtd:    paidInvs.reduce((s, i) => s + i.amount, 0),
    paidCount:   paidInvs.length,
  };

  const newTotal = newInvoice.items.reduce((s, item) => s + item.qty * item.rate, 0);

  async function handleRecordPayment() {
    if (!paymentModal) return;
    setRecordingPayment(true);
    try {
      await api.updateInvoiceStatus(paymentModal.invoice.id, {
        status: "PARTIALLY_PAID",
        payment_amount: parseFloat(paymentModal.amount),
        payment_date: paymentModal.date,
      });
      setInvoices((prev) =>
        prev.map((inv) => {
          if (inv.id !== paymentModal.invoice.id) return inv;
          const newPaid = inv.paid + parseFloat(paymentModal.amount);
          return { ...inv, paid: newPaid, status: newPaid >= inv.amount ? "paid" : "partial" };
        })
      );
      if (selectedInvoice?.id === paymentModal.invoice.id) {
        const newPaid = selectedInvoice.paid + parseFloat(paymentModal.amount);
        setSelectedInvoice({ ...selectedInvoice, paid: newPaid, status: newPaid >= selectedInvoice.amount ? "paid" : "partial" });
      }
      showToast("Payment recorded successfully");
    } catch {
      showToast("Failed to record payment — try again", false);
    } finally {
      setRecordingPayment(false);
      setPaymentModal(null);
    }
  }

  async function handleSendInvoice(asDraft: boolean) {
    if (!companyId) { showToast("Company not loaded", false); return; }
    setSavingInvoice(true);
    try {
      await api.createInvoiceRecord(companyId, {
        type: "ACCOUNTS_RECEIVABLE",
        issue_date: new Date().toISOString().slice(0, 10),
        due_date: newInvoice.due_date || new Date().toISOString().slice(0, 10),
        sub_total: newTotal,
        currency: "INR",
        memo: `${newInvoice.customer} — ${newInvoice.items.map((i) => i.description).join("; ")}`,
      });
      showToast(asDraft ? "Draft saved" : "Invoice sent successfully");
      setShowNewModal(false);
      setNewInvoice({ customer: "", email: "", due_date: "", items: [{ description: "", qty: 1, rate: 0 }] });
    } catch {
      showToast("Failed to save invoice — check connection", false);
    } finally {
      setSavingInvoice(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Invoices" />

      {/* Toast */}
      {toast && (
        <div className={cn(
          "fixed top-4 right-4 z-[100] flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-sm font-semibold transition-all",
          toast.ok ? "bg-emerald-600 text-white" : "bg-red-600 text-white"
        )}>
          {toast.ok ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
          {toast.msg}
        </div>
      )}

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* Hero */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <FileText className="h-3.5 w-3.5" /> Invoice Management
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Invoices & Receivables</h1>
              <p className="mt-1 text-sm text-[#5f5344]">Create, send, and track customer invoices. Automate follow-ups with AI.</p>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => openChat("Analyze outstanding invoices and suggest collection actions")} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <Sparkles className="h-4 w-4" /> AI Collect
              </button>
              <button onClick={() => setShowNewModal(true)} className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                <Plus className="h-4 w-4" /> New Invoice
              </button>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Total Invoiced (Apr)", value: formatCurrency(stats.total),       sub: `${stats.totalCount} invoice${stats.totalCount !== 1 ? "s" : ""}`,             color: "text-[#2a2017]" },
            { label: "Outstanding",          value: formatCurrency(stats.outstanding),  sub: `${stats.outstandingCount} invoice${stats.outstandingCount !== 1 ? "s" : ""}`, color: "text-blue-700" },
            { label: "Overdue",              value: formatCurrency(stats.overdue),       sub: `${stats.overdueCount} invoice${stats.overdueCount !== 1 ? "s" : ""}`,         color: "text-red-600" },
            { label: "Collected MTD",        value: formatCurrency(stats.paid_mtd),     sub: `${stats.paidCount} paid`,                                                      color: "text-emerald-700" },
          ].map((s) => (
            <article key={s.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{s.label}</p>
              <p className={cn("mt-2 text-2xl font-bold", s.color)}>{s.value}</p>
              <p className="mt-1 text-xs text-[#9a8872]">{s.sub}</p>
            </article>
          ))}
        </section>

        {/* Filters + Table */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between border-b border-[#ede8e0]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9a8872]" />
              <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search invoices..." className="rounded-xl border border-[#ddd2c2] bg-[#f9f6f1] py-2 pl-9 pr-4 text-sm w-64 outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {(["all", "draft", "sent", "viewed", "partial", "paid", "overdue"] as const).map((s) => (
                <button key={s} onClick={() => setStatusFilter(s)} className={cn("rounded-full px-3 py-1 text-xs font-semibold border capitalize transition-all", statusFilter === s ? "bg-[#231c15] text-white border-[#231c15]" : "bg-white border-[#ddd2c2] text-[#776b5a] hover:border-[#b8a898]")}>
                  {s === "all" ? "All" : statusMeta[s as InvoiceStatus].label}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#f9f5ef] text-[#776b5a]">
                <tr>
                  {["Invoice #", "Customer", "Date", "Due Date", "Amount", "Balance Due", "Status", "Actions"].map((h) => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-bold uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0ebe3]">
                {filtered.map((inv) => {
                  const meta = statusMeta[inv.status];
                  const StatusIcon = meta.icon;
                  const balance = inv.amount - inv.paid;
                  return (
                    <tr key={inv.id} className="hover:bg-[#fdf9f4] transition-colors">
                      <td className="px-5 py-4 font-mono text-xs font-semibold text-[#8d4f27]">{inv.number}</td>
                      <td className="px-5 py-4">
                        <div>
                          <p className="font-semibold text-[#2a2017]">{inv.customer}</p>
                          <p className="text-xs text-[#9a8872]">{inv.email}</p>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-[#5f5344]">{inv.date}</td>
                      <td className="px-5 py-4 text-[#5f5344]">{inv.due_date}</td>
                      <td className="px-5 py-4 font-semibold text-[#2a2017]">{formatCurrency(inv.amount)}</td>
                      <td className="px-5 py-4">
                        <div>
                          <span className="font-bold" style={{ color: balance > 0 ? "#dc2626" : "#059669" }}>
                            {balance > 0 ? formatCurrency(balance) : "Paid"}
                          </span>
                          {inv.amount > 0 && inv.paid > 0 && balance > 0 && (
                            <div className="mt-1 h-1 w-20 rounded-full bg-[#ede8e0]">
                              <div className="h-1 rounded-full bg-emerald-500" style={{ width: `${Math.round((inv.paid / inv.amount) * 100)}%` }} />
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold border" style={{ color: meta.color, background: meta.bg, borderColor: meta.border }}>
                          <StatusIcon className="h-3 w-3" /> {meta.label}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-1">
                          <button onClick={() => setSelectedInvoice(inv)} className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a]" title="View"><Eye className="h-4 w-4" /></button>
                          <button onClick={() => showToast(`Reminder sent to ${inv.customer}`)} className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a]" title="Send reminder"><Send className="h-4 w-4" /></button>
                          <button onClick={() => exportCSV([inv])} className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a]" title="Download"><Download className="h-4 w-4" /></button>
                          <button
                            onClick={() => setPaymentModal({ invoice: inv, amount: String(inv.amount - inv.paid), date: new Date().toISOString().slice(0, 10) })}
                            className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a]"
                            title="Record payment"
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div className="py-16 text-center text-[#9a8872]">No invoices match your filters.</div>
            )}
          </div>

          <div className="flex items-center justify-between px-5 py-3 border-t border-[#ede8e0] bg-[#faf7f3]">
            <p className="text-xs text-[#9a8872]">Showing {filtered.length} of {invoices.length} invoices</p>
            <div className="flex items-center gap-2">
              <button onClick={() => exportCSV(filtered)} className="rounded-lg border border-[#ddd2c2] bg-white px-3 py-1.5 text-xs font-medium text-[#776b5a] hover:bg-[#f5f0ea] inline-flex items-center gap-1">
                <Download className="h-3.5 w-3.5" /> Export CSV
              </button>
            </div>
          </div>
        </section>

        {/* Aging Summary */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5 sm:p-6">
          <h2 className="text-base font-bold text-[#2a2017] mb-4">AR Aging Summary</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: "Current (0–30 days)", amount: 48700, count: 3, color: "bg-emerald-500" },
              { label: "31–60 days", amount: 7200, count: 1, color: "bg-amber-500" },
              { label: "61–90 days", amount: 0, count: 0, color: "bg-orange-500" },
              { label: "90+ days", amount: 0, count: 0, color: "bg-red-500" },
            ].map((bucket) => (
              <div key={bucket.label} className="rounded-xl border border-[#ede8e0] p-4">
                <div className={cn("w-2 h-2 rounded-full mb-2", bucket.color)} />
                <p className="text-xs text-[#776b5a] mb-1">{bucket.label}</p>
                <p className="text-xl font-bold text-[#2a2017]">{formatCurrency(bucket.amount)}</p>
                <p className="text-xs text-[#9a8872]">{bucket.count} invoice{bucket.count !== 1 ? "s" : ""}</p>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Payment Modal */}
      {paymentModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <div>
                <h2 className="text-lg font-bold text-[#2a2017]">Record Payment</h2>
                <p className="text-sm text-[#776b5a]">{paymentModal.invoice.number} — {paymentModal.invoice.customer}</p>
              </div>
              <button onClick={() => setPaymentModal(null)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Payment Amount (₹)</label>
                <input
                  type="number"
                  value={paymentModal.amount}
                  onChange={(e) => setPaymentModal({ ...paymentModal, amount: e.target.value })}
                  className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Payment Date</label>
                <input
                  type="date"
                  value={paymentModal.date}
                  onChange={(e) => setPaymentModal({ ...paymentModal, date: e.target.value })}
                  className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button onClick={() => setPaymentModal(null)} className="flex-1 rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea]">Cancel</button>
                <button
                  onClick={handleRecordPayment}
                  disabled={recordingPayment || !paymentModal.amount}
                  className="flex-1 rounded-xl bg-[#231c15] py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d] disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <DollarSign className="h-4 w-4" />
                  {recordingPayment ? "Recording…" : "Record Payment"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Invoice Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <h2 className="text-lg font-bold text-[#2a2017]">New Invoice</h2>
              <button onClick={() => setShowNewModal(false)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-5">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Customer *</label>
                  <input value={newInvoice.customer} onChange={(e) => setNewInvoice({ ...newInvoice, customer: e.target.value })} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20" placeholder="Customer name" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Email</label>
                  <input value={newInvoice.email} onChange={(e) => setNewInvoice({ ...newInvoice, email: e.target.value })} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20" placeholder="billing@customer.com" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Invoice Date</label>
                  <input type="date" defaultValue="2026-04-20" className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Due Date</label>
                  <input type="date" value={newInvoice.due_date} onChange={(e) => setNewInvoice({ ...newInvoice, due_date: e.target.value })} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
                </div>
              </div>

              {/* Line Items */}
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Line Items</label>
                <div className="mt-2 rounded-xl border border-[#ddd2c2] overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-[#f9f5ef]">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-bold text-[#776b5a] w-1/2">Description</th>
                        <th className="px-4 py-2 text-right text-xs font-bold text-[#776b5a]">Qty</th>
                        <th className="px-4 py-2 text-right text-xs font-bold text-[#776b5a]">Rate</th>
                        <th className="px-4 py-2 text-right text-xs font-bold text-[#776b5a]">Amount</th>
                        <th className="px-2 py-2" />
                      </tr>
                    </thead>
                    <tbody>
                      {newInvoice.items.map((item, i) => (
                        <tr key={i} className="border-t border-[#f0ebe3]">
                          <td className="px-4 py-2">
                            <input value={item.description} onChange={(e) => { const items = [...newInvoice.items]; items[i].description = e.target.value; setNewInvoice({ ...newInvoice, items }); }} className="w-full bg-transparent text-sm outline-none" placeholder="Service description" />
                          </td>
                          <td className="px-4 py-2">
                            <input type="number" value={item.qty} onChange={(e) => { const items = [...newInvoice.items]; items[i].qty = Number(e.target.value); setNewInvoice({ ...newInvoice, items }); }} className="w-16 bg-transparent text-right text-sm outline-none" />
                          </td>
                          <td className="px-4 py-2">
                            <input type="number" value={item.rate} onChange={(e) => { const items = [...newInvoice.items]; items[i].rate = Number(e.target.value); setNewInvoice({ ...newInvoice, items }); }} className="w-24 bg-transparent text-right text-sm outline-none" />
                          </td>
                          <td className="px-4 py-2 text-right font-semibold text-[#2a2017]">{formatCurrency(item.qty * item.rate)}</td>
                          <td className="px-2 py-2">
                            <button onClick={() => { const items = newInvoice.items.filter((_, j) => j !== i); setNewInvoice({ ...newInvoice, items }); }} className="text-[#c0392b] hover:text-red-700"><X className="h-4 w-4" /></button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <button onClick={() => setNewInvoice({ ...newInvoice, items: [...newInvoice.items, { description: "", qty: 1, rate: 0 }] })} className="mt-2 text-xs font-semibold text-[#8d4f27] hover:text-[#6b3a1e] flex items-center gap-1">
                  <Plus className="h-3.5 w-3.5" /> Add Line Item
                </button>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-[#ede8e0]">
                <div>
                  <p className="text-xs text-[#776b5a]">Subtotal</p>
                  <p className="text-2xl font-bold text-[#2a2017]">{formatCurrency(newTotal)}</p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={() => handleSendInvoice(true)}
                    disabled={savingInvoice}
                    className="rounded-xl border border-[#ddd2c2] px-4 py-2 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea] disabled:opacity-50"
                  >
                    Save Draft
                  </button>
                  <button
                    onClick={() => handleSendInvoice(false)}
                    disabled={savingInvoice || !newInvoice.customer}
                    className="rounded-xl bg-[#231c15] px-4 py-2 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d] inline-flex items-center gap-2 disabled:opacity-50"
                  >
                    <Send className="h-4 w-4" /> {savingInvoice ? "Sending…" : "Send Invoice"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Invoice Detail Drawer */}
      {selectedInvoice && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/30 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md h-full overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <div>
                <p className="text-xs text-[#9a8872] font-mono">{selectedInvoice.number}</p>
                <h2 className="text-lg font-bold text-[#2a2017]">{selectedInvoice.customer}</h2>
              </div>
              <button onClick={() => setSelectedInvoice(null)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-6">
              <div className="flex items-center gap-3">
                {(() => { const meta = statusMeta[selectedInvoice.status]; const Icon = meta.icon; return (
                  <span className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold border" style={{ color: meta.color, background: meta.bg, borderColor: meta.border }}>
                    <Icon className="h-4 w-4" /> {meta.label}
                  </span>
                ); })()}
                <span className="text-sm text-[#776b5a]">Due {selectedInvoice.due_date}</span>
              </div>

              <div className="rounded-xl bg-[#f9f6f1] border border-[#ede8e0] p-4 space-y-2">
                <div className="flex justify-between text-sm"><span className="text-[#776b5a]">Invoice Amount</span><span className="font-semibold">{formatCurrency(selectedInvoice.amount)}</span></div>
                <div className="flex justify-between text-sm"><span className="text-[#776b5a]">Amount Paid</span><span className="font-semibold text-emerald-700">{formatCurrency(selectedInvoice.paid)}</span></div>
                <div className="h-px bg-[#ede8e0] my-1" />
                <div className="flex justify-between text-sm font-bold"><span>Balance Due</span><span className={selectedInvoice.amount - selectedInvoice.paid > 0 ? "text-red-600" : "text-emerald-700"}>{formatCurrency(selectedInvoice.amount - selectedInvoice.paid)}</span></div>
              </div>

              <div>
                <h3 className="text-xs font-bold uppercase tracking-wide text-[#776b5a] mb-3">Line Items</h3>
                {selectedInvoice.items.map((item, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-[#f0ebe3]">
                    <div>
                      <p className="text-sm font-medium text-[#2a2017]">{item.description}</p>
                      <p className="text-xs text-[#9a8872]">{item.qty} × {formatCurrency(item.rate)}</p>
                    </div>
                    <p className="font-semibold text-[#2a2017]">{formatCurrency(item.qty * item.rate)}</p>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => showToast(`Reminder sent to ${selectedInvoice.customer}`)}
                  className="rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea] flex items-center justify-center gap-2"
                >
                  <Mail className="h-4 w-4" /> Send Reminder
                </button>
                <button
                  onClick={() => exportCSV([selectedInvoice])}
                  className="rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea] flex items-center justify-center gap-2"
                >
                  <Download className="h-4 w-4" /> Download CSV
                </button>
                <button
                  onClick={() => {
                    setPaymentModal({
                      invoice: selectedInvoice,
                      amount: String(selectedInvoice.amount - selectedInvoice.paid),
                      date: new Date().toISOString().slice(0, 10),
                    });
                  }}
                  className="rounded-xl bg-[#231c15] text-white py-2.5 text-sm font-medium hover:bg-[#17120d] flex items-center justify-center gap-2"
                >
                  <DollarSign className="h-4 w-4" /> Record Payment
                </button>
                <button
                  onClick={() => showToast(`Invoice ${selectedInvoice.number} duplicated`)}
                  className="rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea] flex items-center justify-center gap-2"
                >
                  <Copy className="h-4 w-4" /> Duplicate
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
