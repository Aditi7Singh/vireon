"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import {
  CheckCircle2, AlertTriangle, Clock, FileText, Sparkles,
  Users, Building2, Download, ChevronRight, Shield,
  CreditCard, ArrowUpRight, Info,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid,
} from "recharts";

const INR = (n: number) =>
  n >= 100_000 ? `₹${(n / 100_000).toFixed(2)}L` : `₹${n.toLocaleString("en-IN")}`;

// ─── Identity ────────────────────────────────────────────────────────────────
const TAN        = "BLRA12345C";
const TAN_CIRCLE = "Bengaluru (A)";
const ENTITY     = "Vireon Seeding Lab Private Limited";
const FY         = "FY 2025-26";

// ─── Quarterly Return Status ─────────────────────────────────────────────────
const QUARTERLY_RETURNS = [
  {
    form: "24Q",
    quarter: "Q1 (Apr–Jun '25)",
    due: "Jul 31 '25",
    filed: "Jul 28 '25",
    challan: "BSR-240728-001",
    tds_amount: 1_284_000,
    status: "filed",
    deductees: 18,
  },
  {
    form: "24Q",
    quarter: "Q2 (Jul–Sep '25)",
    due: "Oct 31 '25",
    filed: "Oct 29 '25",
    challan: "BSR-241029-002",
    tds_amount: 1_302_000,
    status: "filed",
    deductees: 18,
  },
  {
    form: "24Q",
    quarter: "Q3 (Oct–Dec '25)",
    due: "Jan 31 '26",
    filed: "Jan 29 '26",
    challan: "BSR-260129-003",
    tds_amount: 1_319_400,
    status: "filed",
    deductees: 18,
  },
  {
    form: "24Q",
    quarter: "Q4 (Jan–Mar '26)",
    due: "May 31 '26",
    filed: null,
    challan: null,
    tds_amount: 1_336_800,
    status: "upcoming",
    deductees: 18,
  },
  {
    form: "26Q",
    quarter: "Q1 (Apr–Jun '25)",
    due: "Jul 31 '25",
    filed: "Jul 27 '25",
    challan: "BSR-240727-004",
    tds_amount: 182_400,
    status: "filed",
    deductees: 8,
  },
  {
    form: "26Q",
    quarter: "Q2 (Jul–Sep '25)",
    due: "Oct 31 '25",
    filed: "Oct 30 '25",
    challan: "BSR-241030-005",
    tds_amount: 196_800,
    status: "filed",
    deductees: 9,
  },
  {
    form: "26Q",
    quarter: "Q3 (Oct–Dec '25)",
    due: "Jan 31 '26",
    filed: "Jan 28 '26",
    challan: "BSR-260128-006",
    tds_amount: 208_800,
    status: "filed",
    deductees: 10,
  },
  {
    form: "26Q",
    quarter: "Q4 (Jan–Mar '26)",
    due: "May 31 '26",
    filed: null,
    challan: null,
    tds_amount: 220_800,
    status: "upcoming",
    deductees: 10,
  },
];

// ─── Salary TDS per employee (Section 192) ────────────────────────────────────
const SALARY_TDS = [
  { emp: "EMP-001", name: "Aditi Singh",     dept: "Leadership",  gross: 504_000, tds_monthly: 42_000, pan: "ABCPA1234A", form16: "ready",  section: "192" },
  { emp: "EMP-002", name: "Ravi Kumar",      dept: "Leadership",  gross: 336_000, tds_monthly: 28_000, pan: "BCDPK5678B", form16: "ready",  section: "192" },
  { emp: "EMP-003", name: "Nina Roy",        dept: "Leadership",  gross: 312_000, tds_monthly: 26_000, pan: "CDXPR9012C", form16: "ready",  section: "192" },
  { emp: "EMP-004", name: "Kiran Hegde",     dept: "Sprout",      gross: 216_000, tds_monthly: 15_200, pan: "DEFPH3456D", form16: "ready",  section: "192" },
  { emp: "EMP-005", name: "Meena Patil",     dept: "Sprout",      gross: 192_000, tds_monthly: 11_400, pan: "EFGPM7890E", form16: "ready",  section: "192" },
  { emp: "EMP-006", name: "Suresh Gowda",   dept: "Sprout",      gross: 180_000, tds_monthly:  9_600, pan: "FGHSG2345F", form16: "ready",  section: "192" },
  { emp: "EMP-007", name: "Divya Rao",       dept: "Sprout",      gross: 168_000, tds_monthly:  7_800, pan: "GHIDR6789G", form16: "ready",  section: "192" },
  { emp: "EMP-008", name: "Anand Shetty",   dept: "Sprout",      gross: 156_000, tds_monthly:  6_200, pan: "HIJSA1234H", form16: "ready",  section: "192" },
  { emp: "EMP-009", name: "Priya Naik",     dept: "Orchard",     gross: 228_000, tds_monthly: 16_800, pan: "IJKPN5678I", form16: "ready",  section: "192" },
  { emp: "EMP-010", name: "Rohan Desai",    dept: "Orchard",     gross: 204_000, tds_monthly: 13_200, pan: "JKLRD9012J", form16: "ready",  section: "192" },
  { emp: "EMP-011", name: "Seema Joshi",    dept: "Orchard",     gross: 192_000, tds_monthly: 11_400, pan: "KLMSJ3456K", form16: "ready",  section: "192" },
  { emp: "EMP-012", name: "Vijay Kulkarni", dept: "Orchard",     gross: 180_000, tds_monthly:  9_600, pan: "LMNVK7890L", form16: "ready",  section: "192" },
  { emp: "EMP-013", name: "Anjali Mehta",   dept: "Orchard",     gross: 168_000, tds_monthly:  7_800, pan: "MNOAM2345M", form16: "ready",  section: "192" },
  { emp: "EMP-014", name: "Sachin Bhat",    dept: "Orchard",     gross: 156_000, tds_monthly:  6_200, pan: "NOPSB6789N", form16: "ready",  section: "192" },
  { emp: "EMP-015", name: "Lakshmi Iyer",   dept: "AI Lab",      gross: 264_000, tds_monthly: 24_600, pan: "OPQLI1234O", form16: "ready",  section: "192" },
  { emp: "EMP-016", name: "Arun Prasad",    dept: "AI Lab",      gross: 240_000, tds_monthly: 19_200, pan: "PQRAP5678P", form16: "ready",  section: "192" },
  { emp: "EMP-017", name: "Shalini Nair",   dept: "AI Lab",      gross: 216_000, tds_monthly: 15_200, pan: "QRSSN9012Q", form16: "ready",  section: "192" },
  { emp: "EMP-018", name: "Deepak Verma",   dept: "AI Lab",      gross: 204_000, tds_monthly: 13_200, pan: "RSTDV3456R", form16: "ready",  section: "192" },
];

// ─── Non-salary TDS (Section 194C / 194J / 194I) ─────────────────────────────
const VENDOR_TDS = [
  { vendor: "AWS India",          pan: "AAECA0615N", section: "194J", rate: "10%", payment: 4_680_000, tds: 468_000, category: "Technical Services",  form16a: "ready"   },
  { vendor: "Datadog Inc.",       pan: "AAJFD8124Q", section: "194J", rate: "10%", payment: 840_000,   tds: 84_000,  category: "Technical Services",  form16a: "ready"   },
  { vendor: "TLA & Associates",   pan: "AABFT9215K", section: "194J", rate: "10%", payment: 480_000,   tds: 48_000,  category: "Professional Fees",   form16a: "ready"   },
  { vendor: "Office Supplies Co.",pan: "AAACO1234B", section: "194C", rate: "1%",  payment: 360_000,   tds: 3_600,   category: "Contractor Payment",  form16a: "ready"   },
  { vendor: "DivyaSri Properties",pan: "AABGD7812X", section: "194I", rate: "10%", payment: 1_800_000, tds: 180_000, category: "Rent (Land/Bldg)",   form16a: "ready"   },
  { vendor: "CleanPro Services",  pan: "AACCS3219L", section: "194C", rate: "2%",  payment: 300_000,   tds: 6_000,   category: "Contractor Payment",  form16a: "ready"   },
  { vendor: "Kiran Courier",      pan: "AACKC4512M", section: "194C", rate: "1%",  payment: 120_000,   tds: 1_200,   category: "Contractor Payment",  form16a: "pending" },
  { vendor: "LegalEdge LLP",      pan: "AALLE6723P", section: "194J", rate: "10%", payment: 240_000,   tds: 24_000,  category: "Legal Services",      form16a: "ready"   },
];

// ─── Challan payment history ──────────────────────────────────────────────────
const CHALLANS = [
  { challan: "BSR-240415-001", date: "Apr 15 '25", form: "24Q+26Q", amount: 1_484_400, bank: "HDFC Bank",  status: "paid" },
  { challan: "BSR-240715-002", date: "Jul 15 '25", form: "24Q+26Q", amount: 1_499_800, bank: "HDFC Bank",  status: "paid" },
  { challan: "BSR-241015-003", date: "Oct 15 '25", form: "24Q+26Q", amount: 1_516_200, bank: "HDFC Bank",  status: "paid" },
  { challan: "BSR-260115-004", date: "Jan 15 '26", form: "24Q+26Q", amount: 1_528_600, bank: "HDFC Bank",  status: "paid" },
  { challan: "BSR-260415-005", date: "Apr 15 '26", form: "24Q+26Q", amount: 1_557_600, bank: "HDFC Bank",  status: "upcoming" },
];

// ─── Monthly chart data ───────────────────────────────────────────────────────
const MONTHLY_TDS = [
  { month: "Apr '25", salary: 428_000, non_salary: 60_800 },
  { month: "May '25", salary: 434_000, non_salary: 62_400 },
  { month: "Jun '25", salary: 422_000, non_salary: 59_200 },
  { month: "Jul '25", salary: 434_000, non_salary: 65_600 },
  { month: "Aug '25", salary: 434_000, non_salary: 65_600 },
  { month: "Sep '25", salary: 434_000, non_salary: 65_600 },
  { month: "Oct '25", salary: 439_800, non_salary: 69_600 },
  { month: "Nov '25", salary: 439_800, non_salary: 69_600 },
  { month: "Dec '25", salary: 439_800, non_salary: 69_600 },
  { month: "Jan '26", salary: 445_600, non_salary: 73_600 },
  { month: "Feb '26", salary: 445_600, non_salary: 73_600 },
  { month: "Mar '26", salary: 445_600, non_salary: 73_600 },
];

const TOTAL_SALARY_TDS  = SALARY_TDS.reduce((s, e) => s + e.tds_monthly * 12, 0);
const TOTAL_VENDOR_TDS  = VENDOR_TDS.reduce((s, v) => s + v.tds, 0);
const TOTAL_TDS         = TOTAL_SALARY_TDS + TOTAL_VENDOR_TDS;

const STATUS_CHIP: Record<string, { label: string; bg: string; text: string; icon: React.ElementType }> = {
  filed:    { label: "Filed",    bg: "bg-emerald-50",  text: "text-emerald-700", icon: CheckCircle2 },
  upcoming: { label: "Upcoming", bg: "bg-slate-100",   text: "text-slate-600",   icon: Clock },
  pending:  { label: "Pending",  bg: "bg-amber-50",    text: "text-amber-700",   icon: AlertTriangle },
  ready:    { label: "Ready",    bg: "bg-emerald-50",  text: "text-emerald-700", icon: CheckCircle2 },
  paid:     { label: "Paid",     bg: "bg-emerald-50",  text: "text-emerald-700", icon: CheckCircle2 },
};

function StatusChip({ status }: { status: string }) {
  const cfg = STATUS_CHIP[status] ?? STATUS_CHIP.pending;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${cfg.bg} ${cfg.text}`}>
      <Icon className="w-3 h-3" /> {cfg.label}
    </span>
  );
}

const TABS = [
  { id: "returns",   label: "TDS Returns",       icon: FileText  },
  { id: "salary",    label: "Salary TDS (24Q)",   icon: Users     },
  { id: "vendor",    label: "Vendor TDS (26Q)",   icon: Building2 },
  { id: "challans",  label: "Challan Register",   icon: CreditCard},
] as const;
type Tab = typeof TABS[number]["id"];

export default function TDSPage() {
  const [tab, setTab] = useState<Tab>("returns");
  const [deptFilter, setDeptFilter] = useState("All");

  const depts = ["All", "Leadership", "Sprout", "Orchard", "AI Lab"];
  const filteredSalary = deptFilter === "All" ? SALARY_TDS : SALARY_TDS.filter((e) => e.dept === deptFilter);

  const form24 = QUARTERLY_RETURNS.filter((r) => r.form === "24Q");
  const form26 = QUARTERLY_RETURNS.filter((r) => r.form === "26Q");

  return (
    <div className="p-6 space-y-6">
      <TopBar title="TDS Management" subtitle={`${ENTITY} · TAN: ${TAN} · ${TAN_CIRCLE} · ${FY}`} />

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total TDS Deducted",    value: INR(TOTAL_TDS),        sub: "Salary + Non-salary",      color: "text-[#1d1b19]", dot: "bg-emerald-500" },
          { label: "Salary TDS (Sec 192)",  value: INR(TOTAL_SALARY_TDS), sub: "18 employees · Annual",    color: "text-blue-700",  dot: "bg-blue-500"    },
          { label: "Vendor TDS (194C/J/I)", value: INR(TOTAL_VENDOR_TDS), sub: "8 vendors · Annual est.",  color: "text-violet-700",dot: "bg-violet-500"  },
          { label: "Form 16 / 16A Status",  value: "17 / 7",              sub: "Ready · 1 pending",        color: "text-amber-700", dot: "bg-amber-500"   },
        ].map((k) => (
          <div key={k.label} className="bg-white/80 border border-[#e3d6c7] rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className={`w-2 h-2 rounded-full ${k.dot}`} />
              <p className="text-[10px] font-black uppercase tracking-widest text-[#8a7968]">{k.label}</p>
            </div>
            <p className={`text-2xl font-black ${k.color}`}>{k.value}</p>
            <p className="text-[10px] text-[#9e8e7a] mt-0.5">{k.sub}</p>
          </div>
        ))}
      </div>

      {/* Monthly chart */}
      <div className="bg-white/80 border border-[#e3d6c7] rounded-2xl p-5">
        <p className="text-xs font-black uppercase tracking-widest text-[#8a7968] mb-4">Monthly TDS Deduction — FY 2025-26</p>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={MONTHLY_TDS} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0e8de" />
            <XAxis dataKey="month" tick={{ fontSize: 9, fill: "#9e8e7a" }} />
            <YAxis tickFormatter={(v) => `₹${(v / 100000).toFixed(0)}L`} tick={{ fontSize: 9, fill: "#9e8e7a" }} />
            <Tooltip formatter={(v: number) => INR(v)} />
            <Bar dataKey="salary"     name="Salary TDS"    fill="#3b82f6" radius={[3, 3, 0, 0]} stackId="a" />
            <Bar dataKey="non_salary" name="Vendor TDS"    fill="#8b5cf6" radius={[3, 3, 0, 0]} stackId="a" />
          </BarChart>
        </ResponsiveContainer>
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

      {/* ── TDS Returns tab ── */}
      {tab === "returns" && (
        <div className="space-y-5">
          {/* 24Q */}
          <div className="bg-white/80 border border-[#e3d6c7] rounded-2xl overflow-hidden">
            <div className="px-5 py-3 border-b border-[#f0e8de] flex items-center justify-between">
              <div>
                <p className="text-sm font-black text-[#1d1b19]">Form 24Q — Salary TDS Returns</p>
                <p className="text-[10px] text-[#9e8e7a]">Section 192 · 18 employees · Quarterly filing</p>
              </div>
              <span className="text-[10px] bg-blue-50 text-blue-700 font-bold px-2 py-1 rounded-full">4 Quarters</span>
            </div>
            <table className="w-full text-xs">
              <thead className="bg-[#faf5ef]">
                <tr>
                  {["Quarter", "Due Date", "Filed On", "Challan", "Deductees", "TDS Amount", "Status"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-[#9e8e7a]">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {form24.map((r) => (
                  <tr key={r.quarter} className="border-t border-[#f5ede4] hover:bg-[#fdf8f2]">
                    <td className="px-4 py-3 font-semibold text-[#1d1b19]">{r.quarter}</td>
                    <td className="px-4 py-3 text-[#6a6054]">{r.due}</td>
                    <td className="px-4 py-3 text-[#6a6054]">{r.filed ?? "—"}</td>
                    <td className="px-4 py-3 font-mono text-[10px] text-[#8a7968]">{r.challan ?? "—"}</td>
                    <td className="px-4 py-3 text-[#6a6054]">{r.deductees}</td>
                    <td className="px-4 py-3 font-bold text-[#1d1b19]">{INR(r.tds_amount)}</td>
                    <td className="px-4 py-3"><StatusChip status={r.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 26Q */}
          <div className="bg-white/80 border border-[#e3d6c7] rounded-2xl overflow-hidden">
            <div className="px-5 py-3 border-b border-[#f0e8de] flex items-center justify-between">
              <div>
                <p className="text-sm font-black text-[#1d1b19]">Form 26Q — Non-Salary TDS Returns</p>
                <p className="text-[10px] text-[#9e8e7a]">Section 194C / 194J / 194I · Vendor payments · Quarterly filing</p>
              </div>
              <span className="text-[10px] bg-violet-50 text-violet-700 font-bold px-2 py-1 rounded-full">4 Quarters</span>
            </div>
            <table className="w-full text-xs">
              <thead className="bg-[#faf5ef]">
                <tr>
                  {["Quarter", "Due Date", "Filed On", "Challan", "Deductees", "TDS Amount", "Status"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-[#9e8e7a]">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {form26.map((r) => (
                  <tr key={r.quarter} className="border-t border-[#f5ede4] hover:bg-[#fdf8f2]">
                    <td className="px-4 py-3 font-semibold text-[#1d1b19]">{r.quarter}</td>
                    <td className="px-4 py-3 text-[#6a6054]">{r.due}</td>
                    <td className="px-4 py-3 text-[#6a6054]">{r.filed ?? "—"}</td>
                    <td className="px-4 py-3 font-mono text-[10px] text-[#8a7968]">{r.challan ?? "—"}</td>
                    <td className="px-4 py-3 text-[#6a6054]">{r.deductees}</td>
                    <td className="px-4 py-3 font-bold text-[#1d1b19]">{INR(r.tds_amount)}</td>
                    <td className="px-4 py-3"><StatusChip status={r.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Salary TDS tab ── */}
      {tab === "salary" && (
        <div className="bg-white/80 border border-[#e3d6c7] rounded-2xl overflow-hidden">
          <div className="px-5 py-3 border-b border-[#f0e8de] flex items-center justify-between">
            <div>
              <p className="text-sm font-black text-[#1d1b19]">Salary TDS Register — Section 192</p>
              <p className="text-[10px] text-[#9e8e7a]">Monthly deduction per employee · Form 16 ready for all 18</p>
            </div>
            <div className="flex gap-1">
              {depts.map((d) => (
                <button
                  key={d}
                  onClick={() => setDeptFilter(d)}
                  className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all ${
                    deptFilter === d ? "bg-[#1d1b19] text-white" : "bg-[#f6f0e8] text-[#8a7968] hover:text-[#1d1b19]"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>
          <table className="w-full text-xs">
            <thead className="bg-[#faf5ef]">
              <tr>
                {["Emp ID", "Name", "Department", "Monthly Gross", "TDS / Month", "Annual TDS", "PAN", "Sec.", "Form 16"].map((h) => (
                  <th key={h} className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-[#9e8e7a]">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredSalary.map((e) => (
                <tr key={e.emp} className="border-t border-[#f5ede4] hover:bg-[#fdf8f2]">
                  <td className="px-4 py-2.5 font-mono text-[10px] text-[#9e8e7a]">{e.emp}</td>
                  <td className="px-4 py-2.5 font-semibold text-[#1d1b19]">{e.name}</td>
                  <td className="px-4 py-2.5 text-[#6a6054]">{e.dept}</td>
                  <td className="px-4 py-2.5 text-[#6a6054]">{INR(e.gross)}</td>
                  <td className="px-4 py-2.5 font-bold text-[#1d1b19]">{INR(e.tds_monthly)}</td>
                  <td className="px-4 py-2.5 font-bold text-blue-700">{INR(e.tds_monthly * 12)}</td>
                  <td className="px-4 py-2.5 font-mono text-[10px] text-[#8a7968]">{e.pan}</td>
                  <td className="px-4 py-2.5 text-[#6a6054]">{e.section}</td>
                  <td className="px-4 py-2.5"><StatusChip status={e.form16} /></td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-[#fdf8f2] border-t-2 border-[#e3d6c7]">
              <tr>
                <td colSpan={4} className="px-4 py-2.5 text-xs font-black text-[#6a6054]">
                  {filteredSalary.length} employees shown
                </td>
                <td className="px-4 py-2.5 font-black text-[#1d1b19]">
                  {INR(filteredSalary.reduce((s, e) => s + e.tds_monthly, 0))}
                </td>
                <td className="px-4 py-2.5 font-black text-blue-700">
                  {INR(filteredSalary.reduce((s, e) => s + e.tds_monthly * 12, 0))}
                </td>
                <td colSpan={3} />
              </tr>
            </tfoot>
          </table>
        </div>
      )}

      {/* ── Vendor TDS tab ── */}
      {tab === "vendor" && (
        <div className="bg-white/80 border border-[#e3d6c7] rounded-2xl overflow-hidden">
          <div className="px-5 py-3 border-b border-[#f0e8de]">
            <p className="text-sm font-black text-[#1d1b19]">Vendor TDS Register — 194C / 194J / 194I</p>
            <p className="text-[10px] text-[#9e8e7a]">Non-salary payments · Form 16A issued quarterly</p>
          </div>
          <table className="w-full text-xs">
            <thead className="bg-[#faf5ef]">
              <tr>
                {["Vendor", "PAN", "Section", "Rate", "Payment (Annual)", "TDS Deducted", "Category", "Form 16A"].map((h) => (
                  <th key={h} className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-[#9e8e7a]">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {VENDOR_TDS.map((v) => (
                <tr key={v.vendor} className="border-t border-[#f5ede4] hover:bg-[#fdf8f2]">
                  <td className="px-4 py-3 font-semibold text-[#1d1b19]">{v.vendor}</td>
                  <td className="px-4 py-3 font-mono text-[10px] text-[#8a7968]">{v.pan}</td>
                  <td className="px-4 py-3">
                    <span className="bg-violet-50 text-violet-700 text-[10px] font-bold px-2 py-0.5 rounded-full">{v.section}</span>
                  </td>
                  <td className="px-4 py-3 text-[#6a6054]">{v.rate}</td>
                  <td className="px-4 py-3 text-[#6a6054]">{INR(v.payment)}</td>
                  <td className="px-4 py-3 font-bold text-violet-700">{INR(v.tds)}</td>
                  <td className="px-4 py-3 text-[#6a6054]">{v.category}</td>
                  <td className="px-4 py-3"><StatusChip status={v.form16a} /></td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-[#fdf8f2] border-t-2 border-[#e3d6c7]">
              <tr>
                <td colSpan={4} className="px-4 py-2.5 text-xs font-black text-[#6a6054]">
                  {VENDOR_TDS.length} vendors
                </td>
                <td className="px-4 py-2.5 font-black text-[#1d1b19]">
                  {INR(VENDOR_TDS.reduce((s, v) => s + v.payment, 0))}
                </td>
                <td className="px-4 py-2.5 font-black text-violet-700">
                  {INR(VENDOR_TDS.reduce((s, v) => s + v.tds, 0))}
                </td>
                <td colSpan={2} />
              </tr>
            </tfoot>
          </table>
        </div>
      )}

      {/* ── Challans tab ── */}
      {tab === "challans" && (
        <div className="space-y-5">
          <div className="bg-white/80 border border-[#e3d6c7] rounded-2xl overflow-hidden">
            <div className="px-5 py-3 border-b border-[#f0e8de]">
              <p className="text-sm font-black text-[#1d1b19]">Challan Payment Register — ITNS 281</p>
              <p className="text-[10px] text-[#9e8e7a]">TDS remittance by 7th of following month · BSR code tracking</p>
            </div>
            <table className="w-full text-xs">
              <thead className="bg-[#faf5ef]">
                <tr>
                  {["Challan No.", "Payment Date", "Return Form", "Amount", "Bank", "Status"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-[#9e8e7a]">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {CHALLANS.map((c) => (
                  <tr key={c.challan} className="border-t border-[#f5ede4] hover:bg-[#fdf8f2]">
                    <td className="px-4 py-3 font-mono text-[10px] text-[#8a7968]">{c.challan}</td>
                    <td className="px-4 py-3 text-[#6a6054]">{c.date}</td>
                    <td className="px-4 py-3 text-[#6a6054]">{c.form}</td>
                    <td className="px-4 py-3 font-bold text-[#1d1b19]">{INR(c.amount)}</td>
                    <td className="px-4 py-3 text-[#6a6054]">{c.bank}</td>
                    <td className="px-4 py-3"><StatusChip status={c.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Info panel */}
          <div className="bg-blue-50 border border-blue-100 rounded-2xl p-5">
            <div className="flex items-start gap-3">
              <Info className="w-4 h-4 text-blue-600 mt-0.5 shrink-0" />
              <div>
                <p className="text-xs font-black text-blue-800 mb-2">TDS Compliance Summary</p>
                <div className="grid grid-cols-2 gap-x-8 gap-y-1 text-[11px] text-blue-700">
                  <p>✓ TDS deposited by 7th of every month</p>
                  <p>✓ Q1–Q3 returns filed before due dates</p>
                  <p>✓ All salary employees have Form 16 ready</p>
                  <p>✓ 7 of 8 vendors have Form 16A issued</p>
                  <p>✓ PAN verified for all 18 employees</p>
                  <p>⚠ Kiran Courier Form 16A pending</p>
                  <p>✓ No TDS demand outstanding</p>
                  <p>✓ TRACES reconciliation up to date</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Finley panel */}
      <div className="bg-gradient-to-br from-[#1a1410] to-[#2c2218] rounded-2xl p-5 border border-[#3a2d22]">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <p className="text-xs font-black text-white uppercase tracking-widest">Ask Finley about TDS</p>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {[
            "What is our effective TDS rate on salary this FY?",
            "Which vendor has the highest TDS obligation?",
            "Are we at risk for any TDS default interest this quarter?",
            "Show me our TDS vs advance tax net position",
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
