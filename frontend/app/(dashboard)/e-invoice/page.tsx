"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import {
  CheckCircle2, AlertTriangle, Clock, FileText, Sparkles,
  QrCode, Upload, Shield, Info, ChevronRight, Zap,
  ArrowUpRight, Database, RefreshCw,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid,
} from "recharts";

const INR = (n: number) =>
  n >= 100_000 ? `₹${(n / 100_000).toFixed(2)}L` : `₹${n.toLocaleString("en-IN")}`;

// ─── Identity ─────────────────────────────────────────────────────────────────
const GSTIN     = "29AABCS1234A1Z5";
const ENTITY    = "Vireon Seeding Lab Private Limited";
const IRP       = "NIC-IRP-01 (National Informatics Centre)";
const FY        = "FY 2025-26";
const THRESHOLD = "₹5 Crore";

// ─── E-Invoice monthly stats ──────────────────────────────────────────────────
const MONTHLY_STATS = [
  { month: "Apr '25", total: 14, irn_generated: 14, cancelled: 0,  pending: 0,  success_rate: 100 },
  { month: "May '25", total: 15, irn_generated: 15, cancelled: 0,  pending: 0,  success_rate: 100 },
  { month: "Jun '25", total: 16, irn_generated: 16, cancelled: 0,  pending: 0,  success_rate: 100 },
  { month: "Jul '25", total: 17, irn_generated: 17, cancelled: 0,  pending: 0,  success_rate: 100 },
  { month: "Aug '25", total: 18, irn_generated: 18, cancelled: 1,  pending: 0,  success_rate: 100 },
  { month: "Sep '25", total: 19, irn_generated: 19, cancelled: 0,  pending: 0,  success_rate: 100 },
  { month: "Oct '25", total: 20, irn_generated: 20, cancelled: 0,  pending: 0,  success_rate: 100 },
  { month: "Nov '25", total: 21, irn_generated: 21, cancelled: 1,  pending: 0,  success_rate: 100 },
  { month: "Dec '25", total: 22, irn_generated: 22, cancelled: 0,  pending: 0,  success_rate: 100 },
  { month: "Jan '26", total: 23, irn_generated: 23, cancelled: 0,  pending: 0,  success_rate: 100 },
  { month: "Feb '26", total: 24, irn_generated: 22, cancelled: 0,  pending: 2,  success_rate: 92  },
  { month: "Mar '26", total: 25, irn_generated: 23, cancelled: 0,  pending: 2,  success_rate: 92  },
];

// ─── Recent invoices with IRN ─────────────────────────────────────────────────
const RECENT_INVOICES = [
  {
    inv_no: "VSL/2526/0238",
    date: "Mar 28 '26",
    buyer: "Agri-Green Solutions Pvt Ltd",
    gstin_buyer: "29AABCX1234B1Z2",
    taxable: 4_80_000,
    gst: 86_400,
    irn: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f64",
    ack_no: "202603281234560",
    ack_date: "Mar 28 '26 14:23",
    status: "active",
    qr: true,
  },
  {
    inv_no: "VSL/2526/0237",
    date: "Mar 25 '26",
    buyer: "FarmTech India Ltd",
    gstin_buyer: "27AABCF5678C1Z1",
    taxable: 3_60_000,
    gst: 64_800,
    irn: "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
    ack_no: "202603251234561",
    ack_date: "Mar 25 '26 11:05",
    status: "active",
    qr: true,
  },
  {
    inv_no: "VSL/2526/0236",
    date: "Mar 22 '26",
    buyer: "Harvest Digital Pvt Ltd",
    gstin_buyer: "29AABHD9012D1Z5",
    taxable: 5_40_000,
    gst: 97_200,
    irn: "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
    ack_no: "202603221234562",
    ack_date: "Mar 22 '26 09:41",
    status: "active",
    qr: true,
  },
  {
    inv_no: "VSL/2526/0235",
    date: "Mar 19 '26",
    buyer: "Soil Analytics Corp",
    gstin_buyer: "33AABCS3456E1Z3",
    taxable: 2_40_000,
    gst: 43_200,
    irn: "d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
    ack_no: "202603191234563",
    ack_date: "Mar 19 '26 15:17",
    status: "active",
    qr: true,
  },
  {
    inv_no: "VSL/2526/0234",
    date: "Mar 15 '26",
    buyer: "CropAI Technologies",
    gstin_buyer: "29AABCC7890F1Z4",
    taxable: 6_00_000,
    gst: 1_08_000,
    irn: null,
    ack_no: null,
    ack_date: null,
    status: "pending",
    qr: false,
  },
  {
    inv_no: "VSL/2526/0233",
    date: "Mar 12 '26",
    buyer: "GreenField Ventures",
    gstin_buyer: "24AABCG1234G1Z6",
    taxable: 4_20_000,
    gst: 75_600,
    irn: null,
    ack_no: null,
    ack_date: null,
    status: "pending",
    qr: false,
  },
  {
    inv_no: "VSL/2526/0220",
    date: "Nov 08 '25",
    buyer: "Rural Connect Ltd",
    gstin_buyer: "29AABCR2345H1Z7",
    taxable: 3_00_000,
    gst: 54_000,
    irn: "e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5",
    ack_no: "202511081234564",
    ack_date: "Nov 08 '25 12:03",
    status: "cancelled",
    qr: false,
  },
];

// ─── API integration status ───────────────────────────────────────────────────
const API_STATUS = [
  { component: "IRP Authentication",         status: "active",  latency: "142ms",  last_sync: "5 min ago"    },
  { component: "IRN Generation API",         status: "active",  latency: "380ms",  last_sync: "2 min ago"    },
  { component: "QR Code Embed Service",      status: "active",  latency: "95ms",   last_sync: "2 min ago"    },
  { component: "GSTN Upload (GSTR-1 Auto)",  status: "active",  latency: "620ms",  last_sync: "1 hr ago"     },
  { component: "E-Way Bill Integration",     status: "warning", latency: "—",      last_sync: "Not configured"},
  { component: "Webhook (IRN callbacks)",    status: "active",  latency: "—",      last_sync: "Real-time"    },
];

// ─── Compliance timeline ──────────────────────────────────────────────────────
const MANDATE_TIMELINE = [
  { date: "Oct 2020", threshold: "₹500 Cr+", status: "done", desc: "Phase 1 — Large businesses mandatory" },
  { date: "Jan 2021", threshold: "₹100 Cr+", status: "done", desc: "Phase 2 rollout" },
  { date: "Apr 2021", threshold: "₹50 Cr+",  status: "done", desc: "Phase 3 rollout" },
  { date: "Apr 2022", threshold: "₹20 Cr+",  status: "done", desc: "Phase 4 rollout" },
  { date: "Oct 2022", threshold: "₹10 Cr+",  status: "done", desc: "Phase 5 rollout" },
  { date: "Aug 2023", threshold: "₹5 Cr+",   status: "done", desc: "Phase 6 — Vireon now mandatory ✓" },
  { date: "Apr 2025", threshold: "₹1 Cr+",   status: "upcoming", desc: "Expected Phase 7 (proposed)" },
];

const STATUS_CFG: Record<string, { label: string; bg: string; text: string; dot: string }> = {
  active:    { label: "Active",    bg: "bg-emerald-50",  text: "text-emerald-700", dot: "bg-emerald-500" },
  pending:   { label: "Pending",   bg: "bg-amber-50",    text: "text-amber-700",   dot: "bg-amber-400"   },
  cancelled: { label: "Cancelled", bg: "bg-red-50",      text: "text-red-600",     dot: "bg-red-400"     },
  warning:   { label: "Warning",   bg: "bg-amber-50",    text: "text-amber-700",   dot: "bg-amber-400"   },
  done:      { label: "Done",      bg: "bg-emerald-50",  text: "text-emerald-700", dot: "bg-emerald-500" },
  upcoming:  { label: "Upcoming",  bg: "bg-slate-100",   text: "text-slate-600",   dot: "bg-slate-400"   },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CFG[status] ?? STATUS_CFG.pending;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${cfg.bg} ${cfg.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} /> {cfg.label}
    </span>
  );
}

const TABS = [
  { id: "register",  label: "Invoice Register", icon: FileText  },
  { id: "monthly",   label: "Monthly Stats",    icon: BarChart  },
  { id: "api",       label: "API & Integration",icon: Database  },
  { id: "mandate",   label: "Mandate Timeline", icon: Shield    },
] as const;
type Tab = typeof TABS[number]["id"];

const totalIRN       = MONTHLY_STATS.reduce((s, m) => s + m.irn_generated, 0);
const totalInvoices  = MONTHLY_STATS.reduce((s, m) => s + m.total, 0);
const totalCancelled = MONTHLY_STATS.reduce((s, m) => s + m.cancelled, 0);
const totalPending   = MONTHLY_STATS.reduce((s, m) => s + m.pending, 0);

export default function EInvoicePage() {
  const [tab, setTab] = useState<Tab>("register");

  return (
    <div className="p-6 space-y-6">
      <TopBar
        title="E-Invoicing (IRP)"
        subtitle={`${ENTITY} · GSTIN: ${GSTIN} · Turnover threshold: ${THRESHOLD}+ · ${FY}`}
      />

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total Invoices",      value: totalInvoices.toString(),           sub: `${FY} · All B2B`,      dot: "bg-[#b3622d]" },
          { label: "IRN Generated",       value: totalIRN.toString(),                sub: "Acknowledgement sent", dot: "bg-emerald-500" },
          { label: "Cancelled IRNs",      value: totalCancelled.toString(),          sub: "Within 24 hrs",        dot: "bg-red-400"    },
          { label: "Pending IRN",         value: totalPending.toString(),            sub: "Mar '26 — to generate",dot: "bg-amber-400"  },
        ].map((k) => (
          <div key={k.label} className="bg-white/80 border border-[#e3d6c7] rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className={`w-2 h-2 rounded-full ${k.dot}`} />
              <p className="text-[10px] font-black uppercase tracking-widest text-[#8a7968]">{k.label}</p>
            </div>
            <p className="text-2xl font-black text-[#1d1b19]">{k.value}</p>
            <p className="text-[10px] text-[#9e8e7a] mt-0.5">{k.sub}</p>
          </div>
        ))}
      </div>

      {/* IRP Info banner */}
      <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-4 flex items-start gap-3">
        <Shield className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
        <div className="flex-1">
          <p className="text-xs font-black text-emerald-800">E-Invoice Mandate Active · Connected to {IRP}</p>
          <p className="text-[11px] text-emerald-700 mt-0.5">
            All B2B invoices above ₹5 Cr annual turnover are e-invoiced through the IRP portal.
            IRN + QR code embedded on every invoice PDF. Auto-populated in GSTR-1.
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-emerald-700 font-bold bg-white border border-emerald-200 px-3 py-1.5 rounded-xl">
          <CheckCircle2 className="w-3.5 h-3.5" /> Compliant
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-[#f6f0e8] p-1 rounded-xl w-fit">
        {TABS.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                tab === t.id ? "bg-white text-[#1d1b19] shadow-sm" : "text-[#8a7968] hover:text-[#1d1b19]"
              }`}
            >
              <Icon className="w-3.5 h-3.5" /> {t.label}
            </button>
          );
        })}
      </div>

      {/* ── Invoice Register tab ── */}
      {tab === "register" && (
        <div className="bg-white/80 border border-[#e3d6c7] rounded-2xl overflow-hidden">
          <div className="px-5 py-3 border-b border-[#f0e8de] flex items-center justify-between">
            <div>
              <p className="text-sm font-black text-[#1d1b19]">B2B Invoice Register — IRN Status</p>
              <p className="text-[10px] text-[#9e8e7a]">64-character IRN · Ack number · QR code compliance</p>
            </div>
            <button className="flex items-center gap-1.5 text-[11px] text-[#8a7968] bg-[#f6f0e8] px-3 py-1.5 rounded-lg font-bold hover:text-[#1d1b19] transition-all">
              <RefreshCw className="w-3 h-3" /> Sync IRP
            </button>
          </div>
          <table className="w-full text-xs">
            <thead className="bg-[#faf5ef]">
              <tr>
                {["Invoice No.", "Date", "Buyer", "Buyer GSTIN", "Taxable", "GST", "IRN", "Ack No.", "QR", "Status"].map((h) => (
                  <th key={h} className="px-3 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-[#9e8e7a]">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {RECENT_INVOICES.map((inv) => (
                <tr key={inv.inv_no} className="border-t border-[#f5ede4] hover:bg-[#fdf8f2]">
                  <td className="px-3 py-3 font-mono text-[10px] text-[#8a7968]">{inv.inv_no}</td>
                  <td className="px-3 py-3 text-[#6a6054]">{inv.date}</td>
                  <td className="px-3 py-3 font-semibold text-[#1d1b19] max-w-[140px] truncate">{inv.buyer}</td>
                  <td className="px-3 py-3 font-mono text-[10px] text-[#8a7968]">{inv.gstin_buyer}</td>
                  <td className="px-3 py-3 text-[#6a6054]">{INR(inv.taxable)}</td>
                  <td className="px-3 py-3 font-bold text-[#1d1b19]">{INR(inv.gst)}</td>
                  <td className="px-3 py-3">
                    {inv.irn ? (
                      <span className="font-mono text-[9px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
                        {inv.irn.slice(0, 16)}…
                      </span>
                    ) : (
                      <span className="text-[10px] text-amber-600">—</span>
                    )}
                  </td>
                  <td className="px-3 py-3 font-mono text-[10px] text-[#8a7968]">{inv.ack_no ?? "—"}</td>
                  <td className="px-3 py-3">
                    {inv.qr ? (
                      <QrCode className="w-4 h-4 text-emerald-600" />
                    ) : (
                      <span className="text-[10px] text-[#c0a990]">—</span>
                    )}
                  </td>
                  <td className="px-3 py-3"><StatusBadge status={inv.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Monthly Stats tab ── */}
      {tab === "monthly" && (
        <div className="space-y-5">
          <div className="bg-white/80 border border-[#e3d6c7] rounded-2xl p-5">
            <p className="text-xs font-black uppercase tracking-widest text-[#8a7968] mb-4">IRN Generation — Monthly FY 2025-26</p>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={MONTHLY_STATS} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0e8de" />
                <XAxis dataKey="month" tick={{ fontSize: 9, fill: "#9e8e7a" }} />
                <YAxis tick={{ fontSize: 9, fill: "#9e8e7a" }} />
                <Tooltip />
                <Bar dataKey="irn_generated" name="IRN Generated" fill="#10b981" radius={[3, 3, 0, 0]} />
                <Bar dataKey="cancelled"     name="Cancelled"     fill="#f87171" radius={[3, 3, 0, 0]} />
                <Bar dataKey="pending"       name="Pending"       fill="#fbbf24" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white/80 border border-[#e3d6c7] rounded-2xl overflow-hidden">
            <div className="px-5 py-3 border-b border-[#f0e8de]">
              <p className="text-sm font-black text-[#1d1b19]">Monthly Breakdown</p>
            </div>
            <table className="w-full text-xs">
              <thead className="bg-[#faf5ef]">
                <tr>
                  {["Period", "Total Invoices", "IRN Generated", "Cancelled", "Pending", "Success Rate"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-[#9e8e7a]">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {MONTHLY_STATS.map((m) => (
                  <tr key={m.month} className="border-t border-[#f5ede4] hover:bg-[#fdf8f2]">
                    <td className="px-4 py-2.5 font-semibold text-[#1d1b19]">{m.month}</td>
                    <td className="px-4 py-2.5 text-[#6a6054]">{m.total}</td>
                    <td className="px-4 py-2.5 font-bold text-emerald-700">{m.irn_generated}</td>
                    <td className="px-4 py-2.5 text-red-500">{m.cancelled || "—"}</td>
                    <td className="px-4 py-2.5 text-amber-600">{m.pending || "—"}</td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-[#f0e8de] rounded-full h-1.5">
                          <div
                            className={`h-1.5 rounded-full ${m.success_rate === 100 ? "bg-emerald-500" : "bg-amber-400"}`}
                            style={{ width: `${m.success_rate}%` }}
                          />
                        </div>
                        <span className={`text-[10px] font-bold ${m.success_rate === 100 ? "text-emerald-700" : "text-amber-700"}`}>
                          {m.success_rate}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── API & Integration tab ── */}
      {tab === "api" && (
        <div className="space-y-4">
          <div className="bg-white/80 border border-[#e3d6c7] rounded-2xl overflow-hidden">
            <div className="px-5 py-3 border-b border-[#f0e8de]">
              <p className="text-sm font-black text-[#1d1b19]">IRP API Integration Status</p>
              <p className="text-[10px] text-[#9e8e7a]">Connected to NIC IRP · OAuth 2.0 token-based auth · Sandbox + Production</p>
            </div>
            <table className="w-full text-xs">
              <thead className="bg-[#faf5ef]">
                <tr>
                  {["Component", "Status", "Latency", "Last Sync"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-[#9e8e7a]">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {API_STATUS.map((a) => (
                  <tr key={a.component} className="border-t border-[#f5ede4] hover:bg-[#fdf8f2]">
                    <td className="px-4 py-3 font-semibold text-[#1d1b19]">{a.component}</td>
                    <td className="px-4 py-3"><StatusBadge status={a.status} /></td>
                    <td className="px-4 py-3 font-mono text-[11px] text-[#6a6054]">{a.latency}</td>
                    <td className="px-4 py-3 text-[#6a6054]">{a.last_sync}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* E-Invoice workflow */}
          <div className="bg-white/80 border border-[#e3d6c7] rounded-2xl p-5">
            <p className="text-xs font-black uppercase tracking-widest text-[#8a7968] mb-4">E-Invoice Generation Flow</p>
            <div className="flex items-center gap-2 flex-wrap">
              {[
                { step: "1", label: "Invoice Created",     icon: FileText,    color: "bg-blue-100 text-blue-700"    },
                { step: "2", label: "JSON Payload Built",  icon: Database,    color: "bg-violet-100 text-violet-700" },
                { step: "3", label: "IRP Upload",          icon: Upload,      color: "bg-amber-100 text-amber-700"  },
                { step: "4", label: "IRN + Ack Received",  icon: CheckCircle2,color: "bg-emerald-100 text-emerald-700" },
                { step: "5", label: "QR Code Embedded",    icon: QrCode,      color: "bg-teal-100 text-teal-700"    },
                { step: "6", label: "GSTR-1 Auto-filled",  icon: ArrowUpRight,color: "bg-green-100 text-green-700"  },
              ].map((s, i, arr) => {
                const Icon = s.icon;
                return (
                  <div key={s.step} className="flex items-center gap-2">
                    <div className={`flex items-center gap-2 px-3 py-2 rounded-xl text-[11px] font-bold ${s.color}`}>
                      <Icon className="w-3.5 h-3.5" />
                      <span className="font-mono text-[9px] opacity-60">{s.step}.</span>
                      {s.label}
                    </div>
                    {i < arr.length - 1 && <ChevronRight className="w-3.5 h-3.5 text-[#c0b0a0] shrink-0" />}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-amber-50 border border-amber-100 rounded-2xl p-4 flex items-start gap-3">
            <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-xs font-black text-amber-800">E-Way Bill Integration Not Configured</p>
              <p className="text-[11px] text-amber-700 mt-0.5">
                For goods invoices above ₹50,000, an E-Way Bill must be generated alongside the IRN.
                Vireon is a SaaS company (service invoices only) — E-Way Bill is not currently applicable.
                Configure this integration if physical goods shipments are added.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ── Mandate Timeline tab ── */}
      {tab === "mandate" && (
        <div className="space-y-4">
          <div className="bg-white/80 border border-[#e3d6c7] rounded-2xl p-5">
            <p className="text-xs font-black uppercase tracking-widest text-[#8a7968] mb-5">India E-Invoice Mandate Rollout</p>
            <div className="relative">
              <div className="absolute left-[88px] top-0 bottom-0 w-px bg-[#e3d6c7]" />
              <div className="space-y-4">
                {MANDATE_TIMELINE.map((t) => {
                  const cfg = STATUS_CFG[t.status];
                  return (
                    <div key={t.date} className="flex items-start gap-4">
                      <div className="w-[88px] text-right shrink-0">
                        <span className="text-[10px] font-black text-[#9e8e7a]">{t.date}</span>
                      </div>
                      <div className={`relative z-10 w-3 h-3 rounded-full mt-0.5 shrink-0 ${cfg.dot} ring-2 ring-white`} />
                      <div className="flex-1 flex items-center justify-between pb-3">
                        <div>
                          <p className="text-xs font-bold text-[#1d1b19]">{t.desc}</p>
                          <p className="text-[10px] text-[#9e8e7a]">Threshold: {t.threshold} annual turnover</p>
                        </div>
                        <StatusBadge status={t.status} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="bg-white/80 border border-[#e3d6c7] rounded-2xl p-5">
            <p className="text-xs font-black uppercase tracking-widest text-[#8a7968] mb-3">Key E-Invoice Compliance Rules</p>
            <div className="grid grid-cols-2 gap-3">
              {[
                { rule: "IRN Cancellation Window",   detail: "Must cancel within 24 hours of generation only" },
                { rule: "Amendment After IRN",        detail: "Credit/debit note required — direct amendment not allowed" },
                { rule: "IRN Validity",               detail: "IRN is unique and permanent once generated" },
                { rule: "QR Code Mandate",            detail: "Signed QR code must be printed on invoice physically" },
                { rule: "GSTR-1 Auto-population",     detail: "IRP data auto-flows to GSTR-1 Table 4A; manual entry not needed" },
                { rule: "No IRN = Invalid Invoice",   detail: "B2B invoices without IRN are non-compliant under CGST Rules" },
              ].map((c) => (
                <div key={c.rule} className="p-3 bg-[#fdf8f2] border border-[#e8ddd0] rounded-xl">
                  <p className="text-[11px] font-black text-[#1d1b19] mb-0.5">{c.rule}</p>
                  <p className="text-[10px] text-[#9e8e7a]">{c.detail}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Finley panel */}
      <div className="bg-gradient-to-br from-[#1a1410] to-[#2c2218] rounded-2xl p-5 border border-[#3a2d22]">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <p className="text-xs font-black text-white uppercase tracking-widest">Ask Finley about E-Invoicing</p>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {[
            "Which invoices are still pending IRN generation this month?",
            "What happens if I cancel an IRN after 24 hours?",
            "Show me the GST auto-populated from e-invoices into GSTR-1",
            "Are we compliant with the latest CBIC e-invoice circular?",
          ].map((q) => (
            <button
              key={q}
              className="text-left text-[11px] text-amber-200/80 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl px-3 py-2.5 transition-all flex items-start gap-2"
            >
              <ChevronRight className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
