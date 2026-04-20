"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import {
  ShoppingCart, Plus, Search, Sparkles, CheckCircle2, Clock,
  AlertCircle, XCircle, ChevronRight, X, FileText, Eye,
  ThumbsUp, ThumbsDown, Package, DollarSign, BarChart2,
} from "lucide-react";

type POStatus = "draft" | "pending_approval" | "approved" | "sent" | "partially_received" | "received" | "closed" | "cancelled";

interface PurchaseOrder {
  id: string;
  number: string;
  vendor: string;
  category: string;
  created_date: string;
  expected_date: string;
  amount: number;
  received_amount: number;
  status: POStatus;
  requestor: string;
  approver?: string;
  items: { description: string; qty: number; unit_price: number }[];
  invoice_matched?: boolean;
}

const POS: PurchaseOrder[] = [
  { id: "1", number: "PO-2026-042", vendor: "Amazon Web Services", category: "Infrastructure", created_date: "2026-04-01", expected_date: "2026-04-30", amount: 14200, received_amount: 14200, status: "received", requestor: "Aditi Singh", approver: "Aditi Singh", invoice_matched: true, items: [{ description: "EC2 Reserved Instances — 1yr", qty: 4, unit_price: 2800 }, { description: "S3 Storage + Data Transfer", qty: 1, unit_price: 3400 }] },
  { id: "2", number: "PO-2026-043", vendor: "Greenhouse Software", category: "HR / ATS", created_date: "2026-04-05", expected_date: "2026-05-10", amount: 8400, received_amount: 0, status: "approved", requestor: "Priya K.", approver: "Aditi Singh", invoice_matched: false, items: [{ description: "ATS Annual License — 20 seats", qty: 20, unit_price: 420 }] },
  { id: "3", number: "PO-2026-044", vendor: "Figma Inc.", category: "Design Tools", created_date: "2026-04-08", expected_date: "2026-04-20", amount: 2160, received_amount: 0, status: "pending_approval", requestor: "Rahul M.", items: [{ description: "Figma Professional — 12 seats annual", qty: 12, unit_price: 180 }] },
  { id: "4", number: "PO-2026-045", vendor: "Retool", category: "Engineering Tools", created_date: "2026-04-10", expected_date: "2026-05-01", amount: 4800, received_amount: 0, status: "sent", requestor: "Dev Team", approver: "Aditi Singh", items: [{ description: "Retool Business — Annual", qty: 1, unit_price: 4800 }] },
  { id: "5", number: "PO-2026-046", vendor: "Cooley LLP", category: "Legal", created_date: "2026-04-12", expected_date: "2026-04-30", amount: 22500, received_amount: 11250, status: "partially_received", requestor: "Aditi Singh", approver: "Aditi Singh", invoice_matched: false, items: [{ description: "Series A Legal Services — Phase 1", qty: 1, unit_price: 22500 }] },
  { id: "6", number: "PO-2026-047", vendor: "OpenAI", category: "AI / ML", created_date: "2026-04-15", expected_date: "2026-04-30", amount: 3600, received_amount: 0, status: "draft", requestor: "AI Team", items: [{ description: "GPT-4o API Credits — Monthly top-up", qty: 1, unit_price: 3600 }] },
  { id: "7", number: "PO-2026-048", vendor: "Salesforce", category: "CRM", created_date: "2026-04-18", expected_date: "2026-05-18", amount: 8400, received_amount: 0, status: "pending_approval", requestor: "Sales Team", items: [{ description: "Sales Cloud — Enterprise 15 seats Q2", qty: 15, unit_price: 560 }] },
];

const statusMeta: Record<POStatus, { label: string; color: string; bg: string; border: string; icon: React.ElementType }> = {
  draft:                { label: "Draft",              color: "#6b7280", bg: "#f3f4f6", border: "#d1d5db", icon: FileText },
  pending_approval:     { label: "Pending Approval",   color: "#d97706", bg: "#fffbeb", border: "#fde68a", icon: Clock },
  approved:             { label: "Approved",           color: "#2563eb", bg: "#eff6ff", border: "#bfdbfe", icon: CheckCircle2 },
  sent:                 { label: "Sent to Vendor",     color: "#7c3aed", bg: "#f5f3ff", border: "#ddd6fe", icon: Package },
  partially_received:   { label: "Partial Receipt",    color: "#f59e0b", bg: "#fffbeb", border: "#fde68a", icon: BarChart2 },
  received:             { label: "Received",           color: "#059669", bg: "#ecfdf5", border: "#a7f3d0", icon: CheckCircle2 },
  closed:               { label: "Closed",             color: "#6b7280", bg: "#f3f4f6", border: "#d1d5db", icon: CheckCircle2 },
  cancelled:            { label: "Cancelled",          color: "#dc2626", bg: "#fef2f2", border: "#fecaca", icon: XCircle },
};

export default function ProcurementPage() {
  const { openChat } = useAppStore();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<POStatus | "all">("all");
  const [selected, setSelected] = useState<PurchaseOrder | null>(null);
  const [showNew, setShowNew] = useState(false);

  const filtered = POS.filter(po => {
    const matchSearch = po.vendor.toLowerCase().includes(search.toLowerCase()) || po.number.includes(search);
    const matchStatus = statusFilter === "all" || po.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const stats = {
    total: POS.reduce((s, p) => s + p.amount, 0),
    pending: POS.filter(p => p.status === "pending_approval").reduce((s, p) => s + p.amount, 0),
    open: POS.filter(p => !["received", "closed", "cancelled"].includes(p.status)).length,
    notMatched: POS.filter(p => p.status === "received" && !p.invoice_matched).length,
  };

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Procurement" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <ShoppingCart className="h-3.5 w-3.5" /> Purchase Orders
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Procurement & PO Management</h1>
              <p className="mt-1 text-sm text-[#5f5344]">Create POs, manage approvals, track receipt and 3-way match against vendor invoices.</p>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => openChat("Review procurement pipeline and flag any unmatched invoices")} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <Sparkles className="h-4 w-4" /> AI Review
              </button>
              <button onClick={() => setShowNew(true)} className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                <Plus className="h-4 w-4" /> New PO
              </button>
            </div>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Total PO Value (Apr)", value: formatCurrency(stats.total) },
            { label: "Pending Approval", value: formatCurrency(stats.pending), color: "text-amber-700" },
            { label: "Open POs", value: stats.open.toString() },
            { label: "Invoice Unmatched", value: stats.notMatched.toString(), color: stats.notMatched > 0 ? "text-red-600" : "text-emerald-700" },
          ].map(s => (
            <article key={s.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{s.label}</p>
              <p className={cn("mt-2 text-2xl font-bold", s.color || "text-[#2a2017]")}>{s.value}</p>
            </article>
          ))}
        </section>

        {/* 3-Way Match Banner */}
        {stats.notMatched > 0 && (
          <section className="rounded-2xl border border-red-200 bg-red-50 p-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-red-600 shrink-0" />
              <div>
                <p className="text-sm font-bold text-red-900">{stats.notMatched} received PO{stats.notMatched > 1 ? "s" : ""} missing invoice match</p>
                <p className="text-xs text-red-700">3-way matching (PO → Receipt → Invoice) incomplete. Payment should be held.</p>
              </div>
            </div>
          </section>
        )}

        {/* Table */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between border-b border-[#ede8e0]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9a8872]" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search POs..." className="rounded-xl border border-[#ddd2c2] bg-[#f9f6f1] py-2 pl-9 pr-4 text-sm w-64 outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
            </div>
            <div className="flex gap-2 flex-wrap">
              {(["all", "pending_approval", "approved", "sent", "partially_received", "received"] as const).map(s => (
                <button key={s} onClick={() => setStatusFilter(s)} className={cn("rounded-full px-3 py-1 text-xs font-semibold border transition-all", statusFilter === s ? "bg-[#231c15] text-white border-[#231c15]" : "bg-white border-[#ddd2c2] text-[#776b5a] hover:border-[#b8a898]")}>
                  {s === "all" ? "All" : statusMeta[s as POStatus].label}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#f9f5ef] text-[#776b5a]">
                <tr>
                  {["PO #", "Vendor", "Category", "Requestor", "Amount", "Received", "Status", "3-Way", "Actions"].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-bold uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0ebe3]">
                {filtered.map(po => {
                  const meta = statusMeta[po.status];
                  const StatusIcon = meta.icon;
                  const receiptPct = po.amount > 0 ? (po.received_amount / po.amount) * 100 : 0;
                  return (
                    <tr key={po.id} className="hover:bg-[#fdf9f4] transition-colors">
                      <td className="px-5 py-4 font-mono text-xs font-semibold text-[#8d4f27]">{po.number}</td>
                      <td className="px-5 py-4 font-semibold text-[#2a2017]">{po.vendor}</td>
                      <td className="px-5 py-4"><span className="text-xs rounded-full bg-[#f0ebe3] text-[#5f5344] px-2 py-0.5">{po.category}</span></td>
                      <td className="px-5 py-4 text-[#5f5344]">{po.requestor}</td>
                      <td className="px-5 py-4 font-semibold text-[#2a2017]">{formatCurrency(po.amount)}</td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-[#f0ebe3] rounded-full h-1.5">
                            <div className={cn("h-full rounded-full", receiptPct === 100 ? "bg-emerald-500" : receiptPct > 0 ? "bg-amber-500" : "bg-gray-300")} style={{ width: `${receiptPct}%` }} />
                          </div>
                          <span className="text-xs text-[#776b5a]">{receiptPct.toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold border" style={{ color: meta.color, background: meta.bg, borderColor: meta.border }}>
                          <StatusIcon className="h-3 w-3" /> {meta.label}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        {po.status === "received" ? (
                          po.invoice_matched ? (
                            <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700"><CheckCircle2 className="h-3.5 w-3.5" /> Matched</span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-xs font-semibold text-red-600"><AlertCircle className="h-3.5 w-3.5" /> Unmatched</span>
                          )
                        ) : <span className="text-xs text-[#9a8872]">—</span>}
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-1">
                          {po.status === "pending_approval" && (
                            <>
                              <button className="p-1.5 rounded-lg hover:bg-emerald-50 text-emerald-600"><ThumbsUp className="h-4 w-4" /></button>
                              <button className="p-1.5 rounded-lg hover:bg-red-50 text-red-500"><ThumbsDown className="h-4 w-4" /></button>
                            </>
                          )}
                          <button onClick={() => setSelected(po)} className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a]"><Eye className="h-4 w-4" /></button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      {/* PO Detail */}
      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/30 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md h-full overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <div>
                <p className="text-xs font-mono text-[#9a8872]">{selected.number}</p>
                <h2 className="text-lg font-bold text-[#2a2017]">{selected.vendor}</h2>
              </div>
              <button onClick={() => setSelected(null)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-5">
              {(() => { const m = statusMeta[selected.status]; const I = m.icon; return (
                <span className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold border" style={{ color: m.color, background: m.bg, borderColor: m.border }}>
                  <I className="h-4 w-4" /> {m.label}
                </span>
              ); })()}
              <div className="rounded-xl bg-[#f9f6f1] border border-[#ede8e0] p-4 space-y-2">
                {[
                  ["Category", selected.category],
                  ["Requestor", selected.requestor],
                  ["Created", selected.created_date],
                  ["Expected", selected.expected_date],
                  ["PO Amount", formatCurrency(selected.amount)],
                  ["Received", formatCurrency(selected.received_amount)],
                  ...(selected.approver ? [["Approved By", selected.approver]] : []),
                ].map(([l, v]) => (
                  <div key={l} className="flex justify-between text-sm">
                    <span className="text-[#776b5a]">{l}</span>
                    <span className="font-semibold text-[#2a2017]">{v}</span>
                  </div>
                ))}
              </div>
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wide text-[#776b5a] mb-3">Line Items</h3>
                {selected.items.map((item, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-[#f0ebe3]">
                    <div>
                      <p className="text-sm font-medium text-[#2a2017]">{item.description}</p>
                      <p className="text-xs text-[#9a8872]">{item.qty} × {formatCurrency(item.unit_price)}</p>
                    </div>
                    <p className="font-semibold text-[#2a2017]">{formatCurrency(item.qty * item.unit_price)}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
