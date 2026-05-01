"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { cn, formatCurrency } from "@/lib/utils";
import {
  BookMarked, Plus, Search, Download, Filter, Eye,
  CheckCircle2, Clock, AlertCircle, X, Sparkles, ChevronDown,
  ArrowRight, Trash2, Copy,
} from "lucide-react";

type JEStatus = "draft" | "posted" | "pending_approval" | "reversed";

interface JournalLine {
  account: string;
  accountCode: string;
  description: string;
  debit: number;
  credit: number;
}

interface JournalEntry {
  id: string;
  number: string;
  date: string;
  description: string;
  status: JEStatus;
  lines: JournalLine[];
  createdBy: string;
  total: number;
}

const ACCOUNTS = [
  "1000 - Cash & Bank", "1100 - Accounts Receivable", "1200 - Prepaid Expenses",
  "1500 - Property & Equipment", "2000 - Accounts Payable", "2100 - Accrued Liabilities",
  "2500 - Short-term Loans", "3000 - Share Capital", "3100 - Retained Earnings",
  "4000 - Revenue - SaaS", "4100 - Revenue - Professional Services", "4200 - Other Revenue",
  "5000 - Cost of Revenue", "5100 - Engineering Salaries", "5200 - Admin Salaries",
  "5300 - Marketing", "5400 - Rent & Utilities", "5500 - Software & Subscriptions",
  "5600 - Travel & Entertainment", "5700 - Depreciation",
];

const MOCK_ENTRIES: JournalEntry[] = [
  {
    id: "1", number: "JE-2026-0087", date: "2026-04-27", description: "Depreciation - April 2026",
    status: "posted", createdBy: "Finley AI", total: 42500,
    lines: [
      { account: "5700 - Depreciation", accountCode: "5700", description: "Monthly depreciation", debit: 42500, credit: 0 },
      { account: "1500 - Property & Equipment", accountCode: "1500", description: "Accumulated depreciation", debit: 0, credit: 42500 },
    ],
  },
  {
    id: "2", number: "JE-2026-0086", date: "2026-04-26", description: "Prepaid expense amortization",
    status: "posted", createdBy: "Aditi Singh", total: 18000,
    lines: [
      { account: "5500 - Software & Subscriptions", accountCode: "5500", description: "Amortize prepaid Zoom", debit: 18000, credit: 0 },
      { account: "1200 - Prepaid Expenses", accountCode: "1200", description: "Prepaid reduction", debit: 0, credit: 18000 },
    ],
  },
  {
    id: "3", number: "JE-2026-0085", date: "2026-04-25", description: "Accrued salaries - April",
    status: "pending_approval", createdBy: "Finley AI", total: 840000,
    lines: [
      { account: "5100 - Engineering Salaries", accountCode: "5100", description: "April salaries accrual", debit: 840000, credit: 0 },
      { account: "2100 - Accrued Liabilities", accountCode: "2100", description: "Salary payable", debit: 0, credit: 840000 },
    ],
  },
  {
    id: "4", number: "JE-2026-0084", date: "2026-04-24", description: "Revenue recognition - INV-2026-041",
    status: "posted", createdBy: "Finley AI", total: 185000,
    lines: [
      { account: "1100 - Accounts Receivable", accountCode: "1100", description: "Invoice raised", debit: 185000, credit: 0 },
      { account: "4000 - Revenue - SaaS", accountCode: "4000", description: "Q2 revenue recognized", debit: 0, credit: 185000 },
    ],
  },
  {
    id: "5", number: "JE-2026-0083", date: "2026-04-20", description: "Office rent payment",
    status: "posted", createdBy: "Admin", total: 125000,
    lines: [
      { account: "5400 - Rent & Utilities", accountCode: "5400", description: "April rent", debit: 125000, credit: 0 },
      { account: "1000 - Cash & Bank", accountCode: "1000", description: "Bank payment", debit: 0, credit: 125000 },
    ],
  },
  {
    id: "6", number: "JE-2026-0082", date: "2026-04-18", description: "Reverse March accrual",
    status: "reversed", createdBy: "Aditi Singh", total: 65000,
    lines: [
      { account: "2100 - Accrued Liabilities", accountCode: "2100", description: "Reversal", debit: 65000, credit: 0 },
      { account: "5300 - Marketing", accountCode: "5300", description: "Reversal", debit: 0, credit: 65000 },
    ],
  },
];

const STATUS_META: Record<JEStatus, { label: string; color: string; bg: string; border: string; icon: React.ElementType }> = {
  draft:            { label: "Draft",            color: "#6b7280", bg: "#f3f4f6", border: "#d1d5db", icon: Clock },
  posted:           { label: "Posted",           color: "#059669", bg: "#ecfdf5", border: "#a7f3d0", icon: CheckCircle2 },
  pending_approval: { label: "Pending Approval", color: "#d97706", bg: "#fffbeb", border: "#fde68a", icon: Clock },
  reversed:         { label: "Reversed",         color: "#9333ea", bg: "#f5f3ff", border: "#ddd6fe", icon: ArrowRight },
};

const EMPTY_LINE: JournalLine = { account: "", accountCode: "", description: "", debit: 0, credit: 0 };

export default function JournalEntriesPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<JEStatus | "all">("all");
  const [showNewModal, setShowNewModal] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState<JournalEntry | null>(null);
  const [entries, setEntries] = useState<JournalEntry[]>(MOCK_ENTRIES);
  const [newDate, setNewDate] = useState("2026-04-27");
  const [newDesc, setNewDesc] = useState("");
  const [newLines, setNewLines] = useState<JournalLine[]>([{ ...EMPTY_LINE }, { ...EMPTY_LINE }]);

  const filtered = entries.filter(je => {
    const matchSearch = je.number.includes(search) || je.description.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === "all" || je.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const totalDebits = newLines.reduce((s, l) => s + l.debit, 0);
  const totalCredits = newLines.reduce((s, l) => s + l.credit, 0);
  const isBalanced = totalDebits === totalCredits && totalDebits > 0;

  const updateLine = (i: number, field: keyof JournalLine, value: string | number) => {
    const lines = [...newLines];
    (lines[i] as any)[field] = value;
    setNewLines(lines);
  };

  const exportEntries = () => {
    const headers = ["entry_no", "date", "description", "status", "created_by", "total"];
    const rows = entries.map((e) => [e.number, e.date, e.description, e.status, e.createdBy, String(e.total)]);
    const csv = [headers, ...rows]
      .map((row) => row.map((value) => `"${String(value).replace(/"/g, '""')}"`).join(","))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `journal-entries-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const duplicateEntry = (entry: JournalEntry) => {
    const clone: JournalEntry = {
      ...entry,
      id: String(Date.now()),
      number: `JE-2026-${String(entries.length + 90).padStart(4, "0")}`,
      date: new Date().toISOString().slice(0, 10),
      status: "draft",
      createdBy: "Current User",
    };
    setEntries((prev) => [clone, ...prev]);
  };

  const reverseEntry = (entry: JournalEntry) => {
    const reversedLines = entry.lines.map((line) => ({ ...line, debit: line.credit, credit: line.debit }));
    const reversed: JournalEntry = {
      id: String(Date.now()),
      number: `JE-2026-${String(entries.length + 90).padStart(4, "0")}`,
      date: new Date().toISOString().slice(0, 10),
      description: `Reversal: ${entry.description}`,
      status: "reversed",
      lines: reversedLines,
      createdBy: "Current User",
      total: entry.total,
    };
    setEntries((prev) => [reversed, ...prev]);
  };

  const approveEntry = (entry: JournalEntry) => {
    setEntries((prev) => prev.map((e) => e.id === entry.id ? { ...e, status: "posted" as JEStatus } : e));
    setSelectedEntry((prev) => prev ? { ...prev, status: "posted" } : prev);
  };

  const postNewEntry = () => {
    if (!isBalanced || !newDesc.trim()) return;
    const normalizedLines = newLines
      .filter((line) => line.account && (line.debit > 0 || line.credit > 0))
      .map((line) => {
        const accountCode = line.account.split("-")[0]?.trim() || "";
        return { ...line, accountCode };
      });
    if (normalizedLines.length < 2) return;

    const next: JournalEntry = {
      id: String(Date.now()),
      number: `JE-2026-${String(entries.length + 90).padStart(4, "0")}`,
      date: newDate,
      description: newDesc,
      status: "posted",
      lines: normalizedLines,
      createdBy: "Current User",
      total: totalDebits,
    };
    setEntries((prev) => [next, ...prev]);
    setShowNewModal(false);
    setNewDesc("");
    setNewLines([{ ...EMPTY_LINE }, { ...EMPTY_LINE }]);
  };

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Journal Entries" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* Hero */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <BookMarked className="h-3.5 w-3.5" /> General Ledger
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Journal Entries</h1>
              <p className="mt-1 text-sm text-[#5f5344]">
                Post manual journal entries, adjustments, accruals, and reversals directly to the general ledger.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <Sparkles className="h-4 w-4" /> AI Suggest
              </button>
              <button onClick={exportEntries} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <Download className="h-4 w-4" /> Export
              </button>
              <button onClick={() => setShowNewModal(true)} className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                <Plus className="h-4 w-4" /> New Entry
              </button>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="grid gap-4 sm:grid-cols-4">
          {[
            { label: "Total Entries (Apr)", value: entries.length.toString(), sub: "Live ledger list", color: "text-[#2a2017]" },
            { label: "Posted", value: entries.filter(e => e.status === "posted").length.toString(), sub: "Auto + manual", color: "text-emerald-700" },
            { label: "Pending Approval", value: entries.filter(e => e.status === "pending_approval").length.toString(), sub: "Need review", color: "text-amber-600" },
            { label: "Total Debits (Apr)", value: formatCurrency(entries.reduce((sum, e) => sum + e.total, 0)), sub: "Balanced period", color: "text-blue-700" },
          ].map((s) => (
            <article key={s.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{s.label}</p>
              <p className={cn("mt-2 text-2xl font-bold", s.color)}>{s.value}</p>
              <p className="mt-1 text-xs text-[#9a8872]">{s.sub}</p>
            </article>
          ))}
        </section>

        {/* Table */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between border-b border-[#ede8e0]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9a8872]" />
              <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search entries..." className="rounded-xl border border-[#ddd2c2] bg-[#f9f6f1] py-2 pl-9 pr-4 text-sm w-60 outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {(["all", "draft", "posted", "pending_approval", "reversed"] as const).map((s) => (
                <button key={s} onClick={() => setStatusFilter(s)}
                  className={cn("rounded-full px-3 py-1 text-xs font-semibold border capitalize transition-all",
                    statusFilter === s ? "bg-[#231c15] text-white border-[#231c15]" : "bg-white border-[#ddd2c2] text-[#776b5a] hover:border-[#b8a898]"
                  )}>
                  {s === "all" ? "All" : s === "pending_approval" ? "Pending" : STATUS_META[s as JEStatus].label}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#f9f5ef] text-[#776b5a]">
                <tr>
                  {["Entry #", "Date", "Description", "Lines", "Total", "Status", "Created By", "Actions"].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-bold uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0ebe3]">
                {filtered.map((je) => {
                  const meta = STATUS_META[je.status];
                  const StatusIcon = meta.icon;
                  return (
                    <tr key={je.id} className="hover:bg-[#fdf9f4] transition-colors">
                      <td className="px-5 py-4 font-mono text-xs font-semibold text-[#8d4f27]">{je.number}</td>
                      <td className="px-5 py-4 text-[#5f5344]">{je.date}</td>
                      <td className="px-5 py-4">
                        <p className="font-semibold text-[#2a2017] max-w-[200px] truncate">{je.description}</p>
                      </td>
                      <td className="px-5 py-4">
                        <span className="text-xs text-[#9a8872]">{je.lines.length} lines</span>
                      </td>
                      <td className="px-5 py-4 font-semibold text-[#2a2017]">
                        {formatCurrency(je.total)}
                      </td>
                      <td className="px-5 py-4">
                        <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold border"
                          style={{ color: meta.color, background: meta.bg, borderColor: meta.border }}>
                          <StatusIcon className="h-3 w-3" /> {meta.label}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-xs text-[#9a8872]">{je.createdBy}</td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-1">
                          <button onClick={() => setSelectedEntry(je)} className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a]" title="View"><Eye className="h-4 w-4" /></button>
                          <button onClick={() => duplicateEntry(je)} className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a]" title="Copy"><Copy className="h-4 w-4" /></button>
                          {je.status === "posted" && (
                            <button onClick={() => reverseEntry(je)} className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a]" title="Reverse"><ArrowRight className="h-4 w-4" /></button>
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
            <p className="text-xs text-[#9a8872]">Showing {filtered.length} of {entries.length} entries</p>
          </div>
        </section>
      </div>

      {/* New Entry Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <h2 className="text-lg font-bold text-[#2a2017]">New Journal Entry</h2>
              <button onClick={() => setShowNewModal(false)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-5">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Entry Date</label>
                  <input type="date" value={newDate} onChange={e => setNewDate(e.target.value)} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Reference</label>
                  <input className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none" placeholder="Optional reference" />
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Description *</label>
                <input value={newDesc} onChange={e => setNewDesc(e.target.value)} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none" placeholder="e.g. Monthly depreciation - April 2026" />
              </div>

              {/* Lines Table */}
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Journal Lines</label>
                <div className="mt-2 rounded-xl border border-[#ddd2c2] overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-[#f9f5ef]">
                      <tr>
                        <th className="px-4 py-2.5 text-left text-xs font-bold text-[#776b5a] w-2/5">Account</th>
                        <th className="px-4 py-2.5 text-left text-xs font-bold text-[#776b5a] w-1/4">Description</th>
                        <th className="px-4 py-2.5 text-right text-xs font-bold text-[#776b5a]">Debit (₹)</th>
                        <th className="px-4 py-2.5 text-right text-xs font-bold text-[#776b5a]">Credit (₹)</th>
                        <th className="px-2 py-2.5" />
                      </tr>
                    </thead>
                    <tbody>
                      {newLines.map((line, i) => (
                        <tr key={i} className="border-t border-[#f0ebe3]">
                          <td className="px-4 py-2">
                            <select value={line.account} onChange={e => updateLine(i, "account", e.target.value)} className="w-full bg-transparent text-xs outline-none">
                              <option value="">Select account…</option>
                              {ACCOUNTS.map(a => <option key={a} value={a}>{a}</option>)}
                            </select>
                          </td>
                          <td className="px-4 py-2">
                            <input value={line.description} onChange={e => updateLine(i, "description", e.target.value)} className="w-full bg-transparent text-xs outline-none" placeholder="Note" />
                          </td>
                          <td className="px-4 py-2">
                            <input type="number" value={line.debit || ""} onChange={e => updateLine(i, "debit", Number(e.target.value))} className="w-full bg-transparent text-right text-xs outline-none" placeholder="0.00" />
                          </td>
                          <td className="px-4 py-2">
                            <input type="number" value={line.credit || ""} onChange={e => updateLine(i, "credit", Number(e.target.value))} className="w-full bg-transparent text-right text-xs outline-none" placeholder="0.00" />
                          </td>
                          <td className="px-2 py-2">
                            <button onClick={() => setNewLines(newLines.filter((_, j) => j !== i))} className="text-[#c0392b] hover:text-red-700"><X className="h-3.5 w-3.5" /></button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-[#f9f5ef]">
                      <tr>
                        <td colSpan={2} className="px-4 py-2 text-xs font-bold text-[#776b5a]">Totals</td>
                        <td className="px-4 py-2 text-right text-sm font-bold text-[#2a2017]">{formatCurrency(totalDebits)}</td>
                        <td className="px-4 py-2 text-right text-sm font-bold text-[#2a2017]">{formatCurrency(totalCredits)}</td>
                        <td />
                      </tr>
                    </tfoot>
                  </table>
                </div>
                <button onClick={() => setNewLines([...newLines, { ...EMPTY_LINE }])} className="mt-2 text-xs font-semibold text-[#8d4f27] hover:text-[#6b3a1e] flex items-center gap-1">
                  <Plus className="h-3.5 w-3.5" /> Add Line
                </button>
              </div>

              {/* Balance indicator */}
              <div className={cn("rounded-xl border px-4 py-3 flex items-center gap-3",
                isBalanced ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"
              )}>
                {isBalanced
                  ? <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  : <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" />}
                <p className={cn("text-xs font-semibold", isBalanced ? "text-emerald-700" : "text-amber-700")}>
                  {isBalanced
                    ? "Entry is balanced — debits equal credits"
                    : `Out of balance by ${formatCurrency(Math.abs(totalDebits - totalCredits))}`}
                </p>
              </div>

              <div className="flex gap-3 pt-2">
                <button onClick={() => setShowNewModal(false)} className="flex-1 rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea]">Save Draft</button>
                <button onClick={postNewEntry} disabled={!isBalanced} className={cn("flex-1 rounded-xl py-2.5 text-sm font-medium inline-flex items-center justify-center gap-2",
                  isBalanced ? "bg-[#231c15] text-[#fff7eb] hover:bg-[#17120d]" : "bg-gray-200 text-gray-400 cursor-not-allowed"
                )}>
                  <CheckCircle2 className="h-4 w-4" /> Post Entry
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Entry Detail Drawer */}
      {selectedEntry && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/30 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md h-full overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <div>
                <p className="text-xs text-[#9a8872] font-mono">{selectedEntry.number}</p>
                <h2 className="text-base font-bold text-[#2a2017]">{selectedEntry.description}</h2>
              </div>
              <button onClick={() => setSelectedEntry(null)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-5">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[#9a8872]">Date: {selectedEntry.date}</span>
                {(() => { const meta = STATUS_META[selectedEntry.status]; const Icon = meta.icon; return (
                  <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold border"
                    style={{ color: meta.color, background: meta.bg, borderColor: meta.border }}>
                    <Icon className="h-3.5 w-3.5" /> {meta.label}
                  </span>
                ); })()}
              </div>

              <div className="rounded-xl border border-[#ddd2c2] overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-[#f9f5ef]">
                    <tr>
                      <th className="px-4 py-2 text-left font-bold text-[#776b5a]">Account</th>
                      <th className="px-4 py-2 text-right font-bold text-[#776b5a]">Debit</th>
                      <th className="px-4 py-2 text-right font-bold text-[#776b5a]">Credit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedEntry.lines.map((line, i) => (
                      <tr key={i} className="border-t border-[#f0ebe3]">
                        <td className="px-4 py-2.5">
                          <p className="font-semibold text-[#2a2017]">{line.account}</p>
                          <p className="text-[10px] text-[#9a8872]">{line.description}</p>
                        </td>
                        <td className="px-4 py-2.5 text-right text-blue-700 font-semibold">{line.debit > 0 ? formatCurrency(line.debit) : "—"}</td>
                        <td className="px-4 py-2.5 text-right text-[#8d4f27] font-semibold">{line.credit > 0 ? formatCurrency(line.credit) : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-[#f9f5ef]">
                    <tr>
                      <td className="px-4 py-2 font-bold text-xs text-[#776b5a]">Total</td>
                      <td className="px-4 py-2 text-right font-bold text-sm text-[#2a2017]">{formatCurrency(selectedEntry.total)}</td>
                      <td className="px-4 py-2 text-right font-bold text-sm text-[#2a2017]">{formatCurrency(selectedEntry.total)}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              <p className="text-xs text-[#9a8872]">Created by: {selectedEntry.createdBy}</p>

              <div className="grid grid-cols-2 gap-3">
                <button onClick={() => duplicateEntry(selectedEntry)} className="rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea] flex items-center justify-center gap-2">
                  <Copy className="h-4 w-4" /> Duplicate
                </button>
                {selectedEntry.status === "posted" && (
                  <button onClick={() => reverseEntry(selectedEntry)} className="rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea] flex items-center justify-center gap-2">
                    <ArrowRight className="h-4 w-4" /> Reverse
                  </button>
                )}
                {selectedEntry.status === "pending_approval" && (
                  <button onClick={() => approveEntry(selectedEntry)} className="rounded-xl bg-[#231c15] py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d] flex items-center justify-center gap-2">
                    <CheckCircle2 className="h-4 w-4" /> Approve
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
