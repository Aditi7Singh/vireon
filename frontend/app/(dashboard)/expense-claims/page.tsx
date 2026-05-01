"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { cn, formatCurrency } from "@/lib/utils";
import {
  ReceiptText, Plus, Search, Download, Filter, Eye,
  CheckCircle2, Clock, AlertCircle, X, Sparkles, Upload,
  Camera, DollarSign, Users, TrendingUp, FileText,
  ChevronDown, Check, XCircle,
} from "lucide-react";

type ClaimStatus = "draft" | "submitted" | "approved" | "rejected" | "reimbursed";

interface ExpenseClaim {
  id: string;
  claimNumber: string;
  employee: string;
  department: string;
  submittedDate: string;
  amount: number;
  category: string;
  description: string;
  status: ClaimStatus;
  receipts: number;
  approver: string;
}

const MOCK_CLAIMS: ExpenseClaim[] = [
  { id: "1", claimNumber: "EXP-2026-089", employee: "Priya Sharma", department: "Engineering", submittedDate: "2026-04-26", amount: 3850, category: "Travel", description: "Client visit to Bangalore", status: "approved", receipts: 3, approver: "Aditi Singh" },
  { id: "2", claimNumber: "EXP-2026-088", employee: "Rahul Verma", department: "Sales", submittedDate: "2026-04-25", amount: 12400, category: "Client Entertainment", description: "Dinner with Nexus Ventures team", status: "submitted", receipts: 1, approver: "Aditi Singh" },
  { id: "3", claimNumber: "EXP-2026-087", employee: "Ananya Iyer", department: "Product", submittedDate: "2026-04-24", amount: 1200, category: "Software", description: "Figma Pro annual subscription", status: "reimbursed", receipts: 1, approver: "Finley" },
  { id: "4", claimNumber: "EXP-2026-086", employee: "Karan Mehta", department: "Marketing", submittedDate: "2026-04-23", amount: 5600, category: "Travel", description: "SaaStr Annual conference travel", status: "submitted", receipts: 4, approver: "Aditi Singh" },
  { id: "5", claimNumber: "EXP-2026-085", employee: "Deepa Nair", department: "Design", submittedDate: "2026-04-22", amount: 890, category: "Office Supplies", description: "Drawing tablet stylus", status: "approved", receipts: 1, approver: "Finley" },
  { id: "6", claimNumber: "EXP-2026-084", employee: "Aditya Kumar", department: "Engineering", submittedDate: "2026-04-20", amount: 7200, category: "Training", description: "AWS certification course", status: "rejected", receipts: 2, approver: "Aditi Singh" },
  { id: "7", claimNumber: "EXP-2026-083", employee: "Sneha Pillai", department: "HR", submittedDate: "2026-04-18", amount: 2100, category: "Team Building", description: "Team lunch - April onboarding", status: "reimbursed", receipts: 1, approver: "Finley" },
  { id: "8", claimNumber: "EXP-2026-082", employee: "Vikram Singh", department: "Finance", submittedDate: "2026-04-17", amount: 450, category: "Office Supplies", description: "Stationery and printing", status: "reimbursed", receipts: 1, approver: "Aditi Singh" },
];

const STATUS_META: Record<ClaimStatus, { label: string; color: string; bg: string; border: string; icon: React.ElementType }> = {
  draft:       { label: "Draft",       color: "#6b7280", bg: "#f3f4f6", border: "#d1d5db", icon: Clock },
  submitted:   { label: "Submitted",   color: "#2563eb", bg: "#eff6ff", border: "#bfdbfe", icon: Clock },
  approved:    { label: "Approved",    color: "#059669", bg: "#ecfdf5", border: "#a7f3d0", icon: CheckCircle2 },
  rejected:    { label: "Rejected",    color: "#dc2626", bg: "#fef2f2", border: "#fecaca", icon: XCircle },
  reimbursed:  { label: "Reimbursed",  color: "#7c3aed", bg: "#f5f3ff", border: "#ddd6fe", icon: CheckCircle2 },
};

const CATEGORIES = ["Travel", "Client Entertainment", "Software", "Office Supplies", "Training", "Team Building", "Meals", "Other"];
const DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Product", "Design", "HR", "Finance"];

export default function ExpenseClaimsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ClaimStatus | "all">("all");
  const [showNewModal, setShowNewModal] = useState(false);
  const [selectedClaim, setSelectedClaim] = useState<ExpenseClaim | null>(null);
  const [claims, setClaims] = useState<ExpenseClaim[]>(MOCK_CLAIMS);
  const [notice, setNotice] = useState<string | null>(null);

  const [newClaim, setNewClaim] = useState({
    description: "",
    category: "Travel",
    amount: "",
    date: "2026-04-27",
    merchant: "",
    notes: "",
  });

  const filtered = claims.filter(c => {
    const matchSearch = c.employee.toLowerCase().includes(search.toLowerCase()) || c.claimNumber.includes(search) || c.description.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === "all" || c.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const stats = {
    total: claims.reduce((s, c) => s + c.amount, 0),
    pending: claims.filter(c => c.status === "submitted").reduce((s, c) => s + c.amount, 0),
    pendingCount: claims.filter(c => c.status === "submitted").length,
    approved: claims.filter(c => ["approved", "reimbursed"].includes(c.status)).reduce((s, c) => s + c.amount, 0),
    rejected: claims.filter(c => c.status === "rejected").length,
  };

  const handleApprove = (id: string) => {
    setClaims(prev => prev.map(c => c.id === id ? { ...c, status: "approved" as ClaimStatus } : c));
    setSelectedClaim(null);
  };

  const handleReject = (id: string) => {
    setClaims(prev => prev.map(c => c.id === id ? { ...c, status: "rejected" as ClaimStatus } : c));
    setSelectedClaim(null);
  };

  const handleMarkReimbursed = (id: string) => {
    setClaims((prev) => prev.map((c) => c.id === id ? { ...c, status: "reimbursed" as ClaimStatus, approver: "Finance Ops" } : c));
    setSelectedClaim((prev) => prev && prev.id === id ? { ...prev, status: "reimbursed", approver: "Finance Ops" } : prev);
    setNotice("Claim marked as reimbursed.");
  };

  const handleAIAssist = () => {
    const submitted = claims.filter((c) => c.status === "submitted").length;
    setStatusFilter("submitted");
    setNotice(submitted > 0
      ? `AI prioritized ${submitted} submitted claim${submitted > 1 ? "s" : ""} for review.`
      : "No submitted claims found right now.");
  };

  const handleExport = () => {
    const headers = ["claim_number", "employee", "department", "date", "category", "amount", "status", "receipts", "approver", "description"];
    const rows = claims.map((c) => [
      c.claimNumber,
      c.employee,
      c.department,
      c.submittedDate,
      c.category,
      String(c.amount),
      c.status,
      String(c.receipts),
      c.approver,
      c.description,
    ]);
    const csv = [headers, ...rows]
      .map((row) => row.map((value) => `"${String(value).replace(/"/g, '""')}"`).join(","))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `expense-claims-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setNotice("Expense claims exported as CSV.");
  };

  const saveClaim = (status: ClaimStatus) => {
    if (!newClaim.description.trim() || !newClaim.amount.trim()) {
      setNotice("Description and amount are required.");
      return;
    }
    const amount = Number(newClaim.amount);
    if (!Number.isFinite(amount) || amount <= 0) {
      setNotice("Amount must be greater than zero.");
      return;
    }
    const claimNumber = `EXP-${new Date().getFullYear()}-${String(claims.length + 1).padStart(3, "0")}`;
    const created: ExpenseClaim = {
      id: String(Date.now()),
      claimNumber,
      employee: "Current User",
      department: "Finance",
      submittedDate: newClaim.date,
      amount,
      category: newClaim.category,
      description: newClaim.description,
      status,
      receipts: 0,
      approver: status === "draft" ? "Unassigned" : "Aditi Singh",
    };
    setClaims((prev) => [created, ...prev]);
    setShowNewModal(false);
    setNewClaim({
      description: "",
      category: "Travel",
      amount: "",
      date: "2026-04-27",
      merchant: "",
      notes: "",
    });
    setNotice(status === "draft" ? "Expense claim saved as draft." : "Expense claim submitted for approval.");
  };

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Expense Claims" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* Hero */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <ReceiptText className="h-3.5 w-3.5" /> Employee Expenses
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Expense Claims</h1>
              <p className="mt-1 text-sm text-[#5f5344]">
                Submit, approve and reimburse employee expenses. Upload receipts and track reimbursements.
              </p>
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              <button onClick={handleAIAssist} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <Sparkles className="h-4 w-4" /> AI Review
              </button>
              <button onClick={handleExport} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <Download className="h-4 w-4" /> Export
              </button>
              <button onClick={() => setShowNewModal(true)} className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                <Plus className="h-4 w-4" /> New Claim
              </button>
            </div>
          </div>
        </section>

        {notice && (
          <div className="rounded-xl border border-[#ddcfbd] bg-[#fff7ea] px-4 py-3 text-sm text-[#6b4c1e]">
            {notice}
          </div>
        )}

        {/* Stats */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Total Claims (Apr)", value: formatCurrency(stats.total), sub: `${claims.length} claims`, color: "text-[#2a2017]", icon: ReceiptText },
            { label: "Pending Approval", value: formatCurrency(stats.pending), sub: `${stats.pendingCount} claims`, color: "text-amber-600", icon: Clock },
            { label: "Approved & Paid", value: formatCurrency(stats.approved), sub: "This month", color: "text-emerald-700", icon: CheckCircle2 },
            { label: "Rejected", value: stats.rejected.toString(), sub: "Need review", color: "text-red-600", icon: XCircle },
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

        {/* Pending Approvals Banner */}
        {claims.filter(c => c.status === "submitted").length > 0 && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600 shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-bold text-amber-900">{claims.filter(c => c.status === "submitted").length} claims awaiting your approval</p>
              <p className="text-xs text-amber-700 mt-0.5">Total value: {formatCurrency(stats.pending)}</p>
            </div>
            <button onClick={() => setStatusFilter("submitted")} className="text-xs font-bold text-amber-700 hover:text-amber-900 border border-amber-300 px-3 py-1.5 rounded-lg hover:bg-amber-100 transition-colors">
              Review →
            </button>
          </div>
        )}

        {/* Table */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between border-b border-[#ede8e0]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9a8872]" />
              <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search claims, employees..." className="rounded-xl border border-[#ddd2c2] bg-[#f9f6f1] py-2 pl-9 pr-4 text-sm w-64 outline-none focus:ring-2 focus:ring-[#9a5d34]/20" />
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {(["all", "draft", "submitted", "approved", "rejected", "reimbursed"] as const).map((s) => (
                <button key={s} onClick={() => setStatusFilter(s)}
                  className={cn("rounded-full px-3 py-1 text-xs font-semibold border capitalize transition-all",
                    statusFilter === s ? "bg-[#231c15] text-white border-[#231c15]" : "bg-white border-[#ddd2c2] text-[#776b5a] hover:border-[#b8a898]"
                  )}>
                  {s === "all" ? "All" : STATUS_META[s as ClaimStatus].label}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#f9f5ef] text-[#776b5a]">
                <tr>
                  {["Claim #", "Employee", "Department", "Date", "Category", "Amount", "Status", "Actions"].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-bold uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0ebe3]">
                {filtered.map((claim) => {
                  const meta = STATUS_META[claim.status];
                  const StatusIcon = meta.icon;
                  return (
                    <tr key={claim.id} className="hover:bg-[#fdf9f4] transition-colors">
                      <td className="px-5 py-4 font-mono text-xs font-semibold text-[#8d4f27]">{claim.claimNumber}</td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#d97706] to-[#b45309] flex items-center justify-center text-white text-[10px] font-black">
                            {claim.employee.split(" ").map(n => n[0]).join("")}
                          </div>
                          <span className="font-semibold text-[#2a2017]">{claim.employee}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-[#5f5344] text-xs">{claim.department}</td>
                      <td className="px-5 py-4 text-[#5f5344]">{claim.submittedDate}</td>
                      <td className="px-5 py-4">
                        <span className="px-2 py-0.5 bg-[#f0e8dc] text-[#6b4c1e] rounded-md text-xs font-semibold">{claim.category}</span>
                      </td>
                      <td className="px-5 py-4 font-semibold text-[#2a2017]">{formatCurrency(claim.amount)}</td>
                      <td className="px-5 py-4">
                        <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold border"
                          style={{ color: meta.color, background: meta.bg, borderColor: meta.border }}>
                          <StatusIcon className="h-3 w-3" /> {meta.label}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-1">
                          <button onClick={() => setSelectedClaim(claim)} className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a]" title="View">
                            <Eye className="h-4 w-4" />
                          </button>
                          {claim.status === "submitted" && (
                            <>
                              <button onClick={() => handleApprove(claim.id)} className="p-1.5 rounded-lg hover:bg-emerald-50 text-emerald-600" title="Approve">
                                <Check className="h-4 w-4" />
                              </button>
                              <button onClick={() => handleReject(claim.id)} className="p-1.5 rounded-lg hover:bg-red-50 text-red-500" title="Reject">
                                <X className="h-4 w-4" />
                              </button>
                            </>
                          )}
                          {claim.status === "approved" && (
                            <button onClick={() => handleMarkReimbursed(claim.id)} className="p-1.5 rounded-lg hover:bg-purple-50 text-purple-600 text-xs font-semibold px-2" title="Mark Reimbursed">
                              Pay
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {filtered.length === 0 && <div className="py-12 text-center text-[#9a8872]">No claims match your filters.</div>}
          </div>
          <div className="flex items-center justify-between px-5 py-3 border-t border-[#ede8e0] bg-[#faf7f3]">
            <p className="text-xs text-[#9a8872]">Showing {filtered.length} of {claims.length} claims</p>
          </div>
        </section>
      </div>

      {/* New Claim Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <h2 className="text-lg font-bold text-[#2a2017]">New Expense Claim</h2>
              <button onClick={() => setShowNewModal(false)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Date *</label>
                  <input type="date" value={newClaim.date} onChange={e => setNewClaim({...newClaim, date: e.target.value})} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Amount (₹) *</label>
                  <input type="number" value={newClaim.amount} onChange={e => setNewClaim({...newClaim, amount: e.target.value})} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none" placeholder="0.00" />
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Category *</label>
                <select value={newClaim.category} onChange={e => setNewClaim({...newClaim, category: e.target.value})} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none">
                  {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Merchant / Vendor</label>
                <input value={newClaim.merchant} onChange={e => setNewClaim({...newClaim, merchant: e.target.value})} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none" placeholder="e.g. IndiGo Airlines" />
              </div>
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Description *</label>
                <input value={newClaim.description} onChange={e => setNewClaim({...newClaim, description: e.target.value})} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none" placeholder="Purpose of expense" />
              </div>
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Notes</label>
                <textarea value={newClaim.notes} onChange={e => setNewClaim({...newClaim, notes: e.target.value})} rows={2} className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none resize-none" placeholder="Additional context..." />
              </div>

              {/* Receipt upload */}
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Receipts</label>
                <div className="mt-1.5 rounded-xl border-2 border-dashed border-[#d4c3ae] p-5 text-center cursor-pointer hover:border-[#b3622d] hover:bg-[#fff8ec] transition-all">
                  <Camera className="h-8 w-8 text-[#9a8872] mx-auto mb-2" />
                  <p className="text-sm font-semibold text-[#2a2017]">Upload receipt photos</p>
                  <p className="text-xs text-[#9a8872] mt-1">JPG, PNG, PDF · Max 10MB each</p>
                  <button className="mt-3 inline-flex items-center gap-2 rounded-xl bg-[#f0e8dc] px-4 py-2 text-xs font-semibold text-[#6b4c1e]">
                    <Upload className="h-3.5 w-3.5" /> Add Receipts
                  </button>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button onClick={() => saveClaim("draft")} className="flex-1 rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea]">Save Draft</button>
                <button onClick={() => saveClaim("submitted")} className="flex-1 rounded-xl bg-[#231c15] py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d] inline-flex items-center justify-center gap-2">
                  <FileText className="h-4 w-4" /> Submit for Approval
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Claim Detail Drawer */}
      {selectedClaim && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/30 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md h-full overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <div>
                <p className="text-xs text-[#9a8872] font-mono">{selectedClaim.claimNumber}</p>
                <h2 className="text-base font-bold text-[#2a2017]">{selectedClaim.employee}</h2>
              </div>
              <button onClick={() => setSelectedClaim(null)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-5">
              {(() => { const meta = STATUS_META[selectedClaim.status]; const Icon = meta.icon; return (
                <span className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold border"
                  style={{ color: meta.color, background: meta.bg, borderColor: meta.border }}>
                  <Icon className="h-4 w-4" /> {meta.label}
                </span>
              ); })()}

              <div className="rounded-xl bg-[#f9f6f1] border border-[#ede8e0] p-4 space-y-3">
                {[
                  ["Department", selectedClaim.department],
                  ["Date", selectedClaim.submittedDate],
                  ["Category", selectedClaim.category],
                  ["Description", selectedClaim.description],
                  ["Receipts", `${selectedClaim.receipts} attached`],
                  ["Approver", selectedClaim.approver],
                ].map(([label, value]) => (
                  <div key={label} className="flex justify-between text-sm">
                    <span className="text-[#776b5a]">{label}</span>
                    <span className="font-semibold text-[#2a2017]">{value}</span>
                  </div>
                ))}
                <div className="h-px bg-[#ede8e0]" />
                <div className="flex justify-between text-sm font-bold">
                  <span>Total Amount</span>
                  <span className="text-[#2a2017] text-lg">{formatCurrency(selectedClaim.amount)}</span>
                </div>
              </div>

              {selectedClaim.status === "submitted" && (
                <div className="grid grid-cols-2 gap-3">
                  <button onClick={() => handleApprove(selectedClaim.id)} className="rounded-xl bg-emerald-600 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 flex items-center justify-center gap-2">
                    <CheckCircle2 className="h-4 w-4" /> Approve
                  </button>
                  <button onClick={() => handleReject(selectedClaim.id)} className="rounded-xl bg-red-100 border border-red-200 py-2.5 text-sm font-medium text-red-700 hover:bg-red-200 flex items-center justify-center gap-2">
                    <XCircle className="h-4 w-4" /> Reject
                  </button>
                </div>
              )}
              {selectedClaim.status === "approved" && (
                <button onClick={() => handleMarkReimbursed(selectedClaim.id)} className="w-full rounded-xl bg-[#7c3aed] py-2.5 text-sm font-medium text-white hover:bg-[#6d28d9] flex items-center justify-center gap-2">
                  <DollarSign className="h-4 w-4" /> Mark as Reimbursed
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
