"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import {
  CheckCircle2, AlertTriangle, Clock, FileText, Sparkles,
  TrendingUp, ArrowUpRight, ArrowDownRight, Info, Download,
  ChevronRight, Shield,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Cell, PieChart, Pie, Legend,
} from "recharts";

const INR = (n: number) =>
  n >= 100_000 ? `₹${(n / 100_000).toFixed(2)}L` : `₹${n.toLocaleString("en-IN")}`;

// ─── Demo data — realistic for Vireon Seeding Lab (Karnataka, B2B SaaS) ──────

const GSTIN        = "29AABCS1234A1Z5";
const TRADE_NAME   = "Vireon Seeding Lab Private Limited";
const REG_TYPE     = "Regular";
const FY           = "FY 2025-26";
const CURRENT_PERIOD = "March 2026 (Period 12)";

const GSTR1_MONTHS = [
  { period: "Apr '25", invoices: 14, taxable: 1_260_000, igst: 0,       cgst: 113400, sgst: 113400, total: 226800, status: "filed",    due: "May 11 '25" },
  { period: "May '25", invoices: 15, taxable: 1_330_000, igst: 0,       cgst: 119700, sgst: 119700, total: 239400, status: "filed",    due: "Jun 11 '25" },
  { period: "Jun '25", invoices: 16, taxable: 1_410_000, igst: 0,       cgst: 126900, sgst: 126900, total: 253800, status: "filed",    due: "Jul 11 '25" },
  { period: "Jul '25", invoices: 17, taxable: 1_490_000, igst: 48000,   cgst: 111300, sgst: 111300, total: 270600, status: "filed",    due: "Aug 11 '25" },
  { period: "Aug '25", invoices: 18, taxable: 1_570_000, igst: 48000,   cgst: 117300, sgst: 117300, total: 282600, status: "filed",    due: "Sep 11 '25" },
  { period: "Sep '25", invoices: 19, taxable: 1_640_000, igst: 54000,   cgst: 116100, sgst: 116100, total: 286200, status: "filed",    due: "Oct 11 '25" },
  { period: "Oct '25", invoices: 20, taxable: 1_710_000, igst: 72000,   cgst: 114300, sgst: 114300, total: 300600, status: "filed",    due: "Nov 11 '25" },
  { period: "Nov '25", invoices: 21, taxable: 1_790_000, igst: 72000,   cgst: 119100, sgst: 119100, total: 310200, status: "filed",    due: "Dec 11 '25" },
  { period: "Dec '25", invoices: 22, taxable: 1_860_000, igst: 90000,   cgst: 117600, sgst: 117600, total: 325200, status: "filed",    due: "Jan 11 '26" },
  { period: "Jan '26", invoices: 23, taxable: 1_940_000, igst: 90000,   cgst: 122400, sgst: 122400, total: 334800, status: "filed",    due: "Feb 11 '26" },
  { period: "Feb '26", invoices: 24, taxable: 2_010_000, igst: 108000,  cgst: 120600, sgst: 120600, total: 349200, status: "pending",  due: "Mar 11 '26" },
  { period: "Mar '26", invoices: 25, taxable: 2_090_000, igst: 108000,  cgst: 125100, sgst: 125100, total: 358200, status: "upcoming", due: "Apr 11 '26" },
];

// ITC (Input Tax Credit) from eligible purchases
const ITC_SOURCES = [
  { vendor: "Amazon Web Services",    inv: "AWS-2026-03", amount: 4_680_000, tax: 842_400, eligible: true,  category: "Cloud Services" },
  { vendor: "Datadog Inc.",           inv: "DD-2026-03",  amount: 840_000,   tax: 151_200, eligible: true,  category: "Software" },
  { vendor: "GitHub Inc.",            inv: "GH-2026-03",  amount: 600_000,   tax: 108_000, eligible: true,  category: "Software" },
  { vendor: "TLA & Associates",       inv: "TLA-2026-03", amount: 480_000,   tax: 86_400,  eligible: true,  category: "Professional Services" },
  { vendor: "DivyaSri Properties",    inv: "DSP-2026-03", amount: 1_800_000, tax: 0,        eligible: false, category: "Rent (exempt)" },
  { vendor: "CleanPro Services",      inv: "CP-2026-03",  amount: 300_000,   tax: 54_000,  eligible: true,  category: "Services" },
];

const TOTAL_OUTPUT_TAX = GSTR1_MONTHS.reduce((s, m) => s + m.total, 0);
const TOTAL_ITC        = ITC_SOURCES.filter((s) => s.eligible).reduce((s, r) => s + r.tax, 0);
const NET_PAYABLE      = TOTAL_OUTPUT_TAX - TOTAL_ITC;

const GSTR3B_SUMMARY = {
  outward_taxable: GSTR1_MONTHS.reduce((s, m) => s + m.taxable, 0),
  igst_output: GSTR1_MONTHS.reduce((s, m) => s + m.igst, 0),
  cgst_output: GSTR1_MONTHS.reduce((s, m) => s + m.cgst, 0),
  sgst_output: GSTR1_MONTHS.reduce((s, m) => s + m.sgst, 0),
  itc_eligible: TOTAL_ITC,
  net_payable: NET_PAYABLE,
};

const STATUS_META: Record<string, { bg: string; text: string; icon: React.ElementType }> = {
  filed:    { bg: "#dcfce7", text: "#15803d", icon: CheckCircle2 },
  pending:  { bg: "#fef9c3", text: "#a16207", icon: Clock },
  upcoming: { bg: "#f1f5f9", text: "#475569", icon: AlertTriangle },
};

const PIE_DATA = [
  { name: "IGST Collected",    value: GSTR3B_SUMMARY.igst_output, color: "#6366f1" },
  { name: "CGST Collected",    value: GSTR3B_SUMMARY.cgst_output, color: "#f59e0b" },
  { name: "SGST Collected",    value: GSTR3B_SUMMARY.sgst_output, color: "#10b981" },
  { name: "ITC Available",     value: -TOTAL_ITC,                  color: "#34d399" },
];

export default function GSTPage() {
  const { openChat } = useAppStore();
  const [tab, setTab] = useState<"gstr1" | "gstr3b" | "itc">("gstr1");

  const exportGSTNJson = () => {
    const payload = {
      gstin: GSTIN,
      trade_name: TRADE_NAME,
      filing_period: CURRENT_PERIOD,
      fy: FY,
      gstr1: GSTR1_MONTHS,
      gstr3b: GSTR3B_SUMMARY,
      itc_sources: ITC_SOURCES,
      generated_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `gstn-export-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-16 text-[#1d1b17]">
      <TopBar title="GST Compliance" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* ── Hero ── */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.10)] sm:p-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Shield className="h-3.5 w-3.5" />
                GST · Goods & Services Tax · India
              </p>
              <h1 className="mt-3 text-3xl font-bold text-[#2c2013]">GST Compliance Centre</h1>
              <div className="mt-3 flex flex-wrap gap-4 text-xs">
                {[
                  ["GSTIN",        GSTIN],
                  ["Trade Name",   TRADE_NAME],
                  ["Registration", REG_TYPE],
                  ["State",        "Karnataka (29)"],
                  ["Period",       CURRENT_PERIOD],
                ].map(([k, v]) => (
                  <div key={k}>
                    <p className="font-black uppercase tracking-widest text-[#9c8872]" style={{ fontSize: 9 }}>{k}</p>
                    <p className="font-bold text-[#1d1b17]">{v}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* KPI strip */}
            <div className="grid grid-cols-3 gap-3 lg:text-right">
              {[
                { label: "Output Tax Collected",   value: INR(TOTAL_OUTPUT_TAX), color: "#dc2626",  note: `${FY}` },
                { label: "Input Tax Credit (ITC)",  value: INR(TOTAL_ITC),        color: "#15803d",  note: "Eligible purchases" },
                { label: "Net GST Payable",         value: INR(NET_PAYABLE),      color: "#7c3aed",  note: "After ITC offset" },
              ].map(({ label, value, color, note }) => (
                <div key={label} className="rounded-2xl border border-[#ede5d9] bg-white/80 px-4 py-3">
                  <p className="text-[9px] font-black uppercase tracking-widest text-[#9c8872]">{label}</p>
                  <p className="text-lg font-black" style={{ color }}>{value}</p>
                  <p className="text-[9px] text-[#b08a5c]">{note}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 flex gap-2">
            <button
              onClick={() => openChat("What is our GST liability for this quarter? Calculate net payable after ITC and tell me the due date for GSTR-3B filing.")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#1f1a16] px-4 py-2.5 text-xs font-bold text-[#fff6ea] hover:bg-[#14110f] transition-all"
            >
              <Sparkles className="h-3.5 w-3.5 text-amber-300" />
              Ask Finley to calculate GST liability
            </button>
            <button
              onClick={() => openChat("Generate GSTR-3B summary for the current month with ITC reconciliation")}
              className="inline-flex items-center gap-2 rounded-xl border border-[#d9c9b4] bg-white px-4 py-2.5 text-xs font-bold text-[#5f4c38] hover:bg-[#fdf6eb] transition-all"
            >
              <FileText className="h-3.5 w-3.5" />
              Generate GSTR-3B draft
            </button>
          </div>
        </section>

        {/* ── Tabs ── */}
        <div className="flex gap-2">
          {([["gstr1","GSTR-1 (Outward Supplies)"], ["gstr3b","GSTR-3B (Summary Return)"], ["itc","Input Tax Credit"]] as const).map(([t, label]) => (
            <button key={t} onClick={() => setTab(t)}
              className={`rounded-xl px-4 py-2 text-xs font-bold transition-all ${tab === t ? "bg-[#1f1a16] text-[#fff6ea]" : "bg-white border border-[#e0d4c6] text-[#6b5948] hover:bg-[#fdf6eb]"}`}>
              {label}
            </button>
          ))}
        </div>

        {/* ── GSTR-1 TAB ── */}
        {tab === "gstr1" && (
          <section className="rounded-3xl border border-[#d9cdbc] bg-white overflow-hidden shadow-[0_4px_24px_rgba(63,45,24,0.06)]">
            <div className="flex items-center justify-between border-b border-[#f0e8dc] px-6 py-4">
              <div>
                <h2 className="text-base font-bold text-[#1d1b17]">GSTR-1 — Outward Supply Register</h2>
                <p className="text-xs text-[#9c8c7c]">Monthly statement of outward taxable supplies · FY 2025-26</p>
              </div>
              <button onClick={exportGSTNJson} className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9c9b4] bg-[#faf7f3] px-3 py-1.5 text-xs font-bold text-[#6b5948]">
                <Download className="h-3.5 w-3.5" />
                Export JSON (GSTN format)
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-[#f0e8dc] bg-[#faf7f3]">
                    {["Period", "Invoices", "Taxable Value", "IGST", "CGST", "SGST", "Total Tax", "Due Date", "Status"].map((h) => (
                      <th key={h} className="px-4 py-3 text-[9px] font-black uppercase tracking-widest text-[#9c8c7c] whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {GSTR1_MONTHS.map((row) => {
                    const meta = STATUS_META[row.status];
                    const Icon = meta.icon;
                    return (
                      <tr key={row.period} className="border-b border-[#f7f3ef] hover:bg-[#fdf9f4] transition-colors">
                        <td className="px-4 py-3 text-xs font-bold text-[#1d1b17]">{row.period}</td>
                        <td className="px-4 py-3 text-xs text-[#6b5948]">{row.invoices}</td>
                        <td className="px-4 py-3 text-xs font-semibold text-[#1d1b17]">{INR(row.taxable)}</td>
                        <td className="px-4 py-3 text-xs text-[#6366f1]">{row.igst > 0 ? INR(row.igst) : "—"}</td>
                        <td className="px-4 py-3 text-xs text-[#f59e0b]">{INR(row.cgst)}</td>
                        <td className="px-4 py-3 text-xs text-[#10b981]">{INR(row.sgst)}</td>
                        <td className="px-4 py-3 text-xs font-black text-[#1d1b17]">{INR(row.total)}</td>
                        <td className="px-4 py-3 text-[10px] text-[#9c8c7c]">{row.due}</td>
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[9px] font-bold"
                            style={{ background: meta.bg, color: meta.text }}>
                            <Icon className="h-2.5 w-2.5" />
                            {row.status.charAt(0).toUpperCase() + row.status.slice(1)}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  <tr className="bg-[#faf7f3] border-t border-[#e8dfd4] font-black">
                    <td className="px-4 py-3 text-xs text-[#1d1b17]">FY Total</td>
                    <td className="px-4 py-3 text-xs text-[#1d1b17]">{GSTR1_MONTHS.reduce((s, m) => s + m.invoices, 0)}</td>
                    <td className="px-4 py-3 text-xs text-[#1d1b17]">{INR(GSTR3B_SUMMARY.outward_taxable)}</td>
                    <td className="px-4 py-3 text-xs text-[#6366f1]">{INR(GSTR3B_SUMMARY.igst_output)}</td>
                    <td className="px-4 py-3 text-xs text-[#f59e0b]">{INR(GSTR3B_SUMMARY.cgst_output)}</td>
                    <td className="px-4 py-3 text-xs text-[#10b981]">{INR(GSTR3B_SUMMARY.sgst_output)}</td>
                    <td className="px-4 py-3 text-xs text-[#dc2626]">{INR(TOTAL_OUTPUT_TAX)}</td>
                    <td colSpan={2} />
                  </tr>
                </tfoot>
              </table>
            </div>
          </section>
        )}

        {/* ── GSTR-3B TAB ── */}
        {tab === "gstr3b" && (
          <div className="space-y-5">
            {/* Summary cards */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[
                { label: "3.1 — Outward taxable supplies",    value: GSTR3B_SUMMARY.outward_taxable,  note: "B2B + B2C (18% GST)", color: "#dc2626" },
                { label: "4A — ITC available (eligible)",     value: GSTR3B_SUMMARY.itc_eligible,     note: "Auto-populated from 2A/2B", color: "#15803d" },
                { label: "6.1 — Net GST payable",            value: GSTR3B_SUMMARY.net_payable,      note: "3.1 tax minus 4A ITC", color: "#7c3aed" },
                { label: "IGST (inter-state supply)",         value: GSTR3B_SUMMARY.igst_output,      note: "Section 7(5) IGST Act", color: "#6366f1" },
                { label: "CGST (intra-state — centre)",       value: GSTR3B_SUMMARY.cgst_output,      note: "50% of SGST+CGST", color: "#f59e0b" },
                { label: "SGST (intra-state — state)",        value: GSTR3B_SUMMARY.sgst_output,      note: "Karnataka state tax", color: "#10b981" },
              ].map(({ label, value, note, color }) => (
                <div key={label} className="rounded-2xl border border-[#ede5d9] bg-white p-4 shadow-sm">
                  <p className="text-[9px] font-black uppercase tracking-widest text-[#9c8c7c]" style={{ color }}>{label}</p>
                  <p className="mt-1 text-xl font-black text-[#1d1b17]">{INR(value)}</p>
                  <p className="text-[10px] text-[#b08a5c]">{note}</p>
                </div>
              ))}
            </div>

            {/* Liability visualisation */}
            <section className="grid gap-5 lg:grid-cols-2">
              <div className="rounded-3xl border border-[#d9cdbc] bg-white p-5">
                <p className="mb-3 text-sm font-bold text-[#1d1b17]">Monthly Tax Collection — FY 2025-26</p>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={GSTR1_MONTHS.slice(0, 10)} barSize={16}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0e8dc" vertical={false} />
                    <XAxis dataKey="period" tick={{ fontSize: 9, fill: "#9c8c7c" }} axisLine={false} tickLine={false} />
                    <YAxis tickFormatter={(v) => `₹${(v / 100000).toFixed(0)}L`} tick={{ fontSize: 9, fill: "#9c8c7c" }} axisLine={false} tickLine={false} />
                    <Tooltip formatter={(v: number) => [INR(v)]} contentStyle={{ borderRadius: 10, border: "1px solid #e0d4c6", fontSize: 11 }} />
                    <Bar dataKey="igst"  fill="#6366f1" stackId="a" name="IGST"  radius={[0,0,0,0]} />
                    <Bar dataKey="cgst"  fill="#f59e0b" stackId="a" name="CGST" />
                    <Bar dataKey="sgst"  fill="#10b981" stackId="a" name="SGST"  radius={[4,4,0,0]} />
                    <Legend wrapperStyle={{ fontSize: 10 }} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="rounded-3xl border border-[#d9cdbc] bg-white p-5">
                <p className="mb-3 text-sm font-bold text-[#1d1b17]">Output vs ITC — Net Liability</p>
                <div className="flex flex-col gap-3 justify-center h-[200px] px-4">
                  {[
                    { label: "Total Output Tax",  val: TOTAL_OUTPUT_TAX, color: "#dc2626",  pct: 100 },
                    { label: "ITC Available",     val: -TOTAL_ITC,       color: "#15803d",  pct: Math.round(TOTAL_ITC / TOTAL_OUTPUT_TAX * 100) },
                    { label: "Net Payable",        val: NET_PAYABLE,      color: "#7c3aed",  pct: Math.round(NET_PAYABLE / TOTAL_OUTPUT_TAX * 100) },
                  ].map(({ label, val, color, pct }) => (
                    <div key={label}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="font-semibold text-[#6b5948]">{label}</span>
                        <span className="font-black" style={{ color }}>{INR(Math.abs(val))}</span>
                      </div>
                      <div className="h-2 rounded-full bg-[#f0e8dc] overflow-hidden">
                        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: color }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </div>
        )}

        {/* ── ITC TAB ── */}
        {tab === "itc" && (
          <section className="rounded-3xl border border-[#d9cdbc] bg-white overflow-hidden shadow-[0_4px_24px_rgba(63,45,24,0.06)]">
            <div className="border-b border-[#f0e8dc] px-6 py-4">
              <h2 className="text-base font-bold text-[#1d1b17]">Input Tax Credit Register</h2>
              <p className="text-xs text-[#9c8c7c]">Eligible ITC from purchase invoices under Section 16 — CGST Act 2017</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-[#f0e8dc] bg-[#faf7f3]">
                    {["Vendor", "Invoice No.", "Category", "Taxable Amt", "GST Paid", "ITC Eligible", "Status"].map((h) => (
                      <th key={h} className="px-4 py-3 text-[9px] font-black uppercase tracking-widest text-[#9c8c7c]">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ITC_SOURCES.map((r) => (
                    <tr key={r.inv} className="border-b border-[#f7f3ef] hover:bg-[#fdf9f4] transition-colors">
                      <td className="px-4 py-3 text-xs font-semibold text-[#1d1b17]">{r.vendor}</td>
                      <td className="px-4 py-3 text-xs font-mono text-[#6b5948]">{r.inv}</td>
                      <td className="px-4 py-3">
                        <span className="rounded-lg bg-[#f3ede6] px-2 py-0.5 text-[10px] font-bold text-[#6b5948]">{r.category}</span>
                      </td>
                      <td className="px-4 py-3 text-xs text-[#1d1b17]">{INR(r.amount)}</td>
                      <td className="px-4 py-3 text-xs font-black text-[#dc2626]">{r.tax > 0 ? INR(r.tax) : "—"}</td>
                      <td className="px-4 py-3 text-xs font-black" style={{ color: r.eligible ? "#15803d" : "#9c8c7c" }}>
                        {r.eligible ? INR(r.tax) : "Blocked"}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-2 py-0.5 text-[9px] font-bold ${r.eligible ? "bg-[#dcfce7] text-[#15803d]" : "bg-[#f1f5f9] text-[#64748b]"}`}>
                          {r.eligible ? "Claimable" : "Blocked (Sec 17(5))"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-[#faf7f3] border-t border-[#e8dfd4]">
                    <td colSpan={5} className="px-4 py-3 text-xs font-black text-[#1d1b17]">Total ITC Available (FY 2025-26)</td>
                    <td className="px-4 py-3 text-xs font-black text-[#15803d]">{INR(TOTAL_ITC)}</td>
                    <td />
                  </tr>
                </tfoot>
              </table>
            </div>
            <div className="border-t border-[#f0e8dc] bg-[#faf7f3] px-6 py-4">
              <div className="flex items-start gap-2 text-xs text-[#6b5948]">
                <Info className="h-3.5 w-3.5 mt-0.5 shrink-0 text-[#b08a5c]" />
                <p>ITC on rent is blocked under Section 17(5)(c) — CGST Act. ITC on eligible services (cloud, software, professional) is claimable per Section 16. Always reconcile with GSTR-2A/2B before filing.</p>
              </div>
            </div>
          </section>
        )}

        {/* ── Finley GST prompts ── */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(135deg,#1f1a16,#2e231a)] p-5">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-black uppercase tracking-widest text-amber-400">Finley · GST Intelligence</p>
              <p className="mt-1 text-sm font-bold text-white">Let Finley prepare your GST returns</p>
              <p className="mt-1 text-xs text-[#c8b89e]">End-to-end from invoice data to GSTN-ready JSON payload</p>
            </div>
            <div className="flex flex-col gap-2 sm:items-end">
              {["Reconcile GSTR-2A with our purchase register","Identify invoices missing HSN/SAC codes","Calculate reversals under Rule 37 (unpaid invoices > 180 days)"].map((q) => (
                <button key={q} onClick={() => openChat(q)}
                  className="rounded-xl border border-[#4a3c2e] bg-[#2e2419]/60 px-3 py-2 text-left text-[11px] text-[#e8d9c6] hover:bg-[#3d3025]/60 transition-all">{q}</button>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
