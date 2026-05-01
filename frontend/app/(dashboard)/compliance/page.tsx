"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import {
  Calendar, Sparkles, CheckCircle2, AlertCircle, Clock,
  AlertTriangle, ChevronRight, Globe, Shield, FileText,
  Building2, DollarSign, Users,
} from "lucide-react";

type EventStatus = "completed" | "upcoming" | "due_soon" | "overdue";
type EventCategory = "tax" | "payroll" | "corporate" | "compliance" | "banking";

interface ComplianceEvent {
  id: string;
  title: string;
  description: string;
  due_date: string;
  jurisdiction: string;
  category: EventCategory;
  status: EventStatus;
  priority: "critical" | "high" | "medium" | "low";
  form?: string;
  auto_file?: boolean;
}

const EVENTS: ComplianceEvent[] = [
  { id: "1", title: "Federal Corporate Tax Extension", description: "Form 7004 extension filing for FY 2025 corporate income tax return", due_date: "2026-04-15", jurisdiction: "US Federal", category: "tax", status: "completed", priority: "critical", form: "Form 7004" },
  { id: "2", title: "Q1 2026 Estimated Tax Payment", description: "Federal quarterly estimated income tax payment for Q1 2026", due_date: "2026-04-15", jurisdiction: "US Federal", category: "tax", status: "completed", priority: "critical", form: "Form 1120-W" },
  { id: "3", title: "California Q1 State Estimated Tax", description: "California state quarterly estimated corporate tax payment", due_date: "2026-04-15", jurisdiction: "California", category: "tax", status: "completed", priority: "high", form: "Form 100-ES" },
  { id: "4", title: "April Payroll Tax Deposit", description: "Semi-weekly federal payroll tax deposit (FICA + income withholding)", due_date: "2026-04-22", jurisdiction: "US Federal", category: "payroll", status: "due_soon", priority: "critical", form: "Form 941" },
  { id: "5", title: "FBAR Filing (Foreign Bank Accounts)", description: "Report of Foreign Bank and Financial Accounts if accounts exceed $10k", due_date: "2026-04-30", jurisdiction: "FinCEN", category: "banking", status: "upcoming", priority: "high", form: "FinCEN 114" },
  { id: "6", title: "Annual Delaware Franchise Tax", description: "Annual Delaware franchise tax due based on authorized shares method", due_date: "2026-06-01", jurisdiction: "Delaware", category: "corporate", status: "upcoming", priority: "high" },
  { id: "7", title: "Q2 Estimated Federal Tax", description: "Second quarter estimated federal corporate income tax", due_date: "2026-06-15", jurisdiction: "US Federal", category: "tax", status: "upcoming", priority: "critical", form: "Form 1120-W" },
  { id: "8", title: "SOC 2 Type II Surveillance Audit", description: "Annual SOC 2 Type II surveillance audit for security compliance", due_date: "2026-07-15", jurisdiction: "AICPA", category: "compliance", status: "upcoming", priority: "high" },
  { id: "9", title: "Q3 Estimated Federal Tax", description: "Third quarter estimated federal corporate income tax", due_date: "2026-09-15", jurisdiction: "US Federal", category: "tax", status: "upcoming", priority: "critical", form: "Form 1120-W" },
  { id: "10", title: "Annual 409A Valuation Refresh", description: "Independent 409A valuation required for stock option grants compliance", due_date: "2026-10-01", jurisdiction: "IRS / SEC", category: "compliance", status: "upcoming", priority: "high" },
  { id: "11", title: "Q4 Estimated Federal Tax", description: "Fourth quarter estimated federal corporate income tax", due_date: "2026-12-15", jurisdiction: "US Federal", category: "tax", status: "upcoming", priority: "critical", form: "Form 1120-W" },
  { id: "12", title: "FY 2026 Corporate Tax Return", description: "Federal corporate income tax return filing (or 6-month extension)", due_date: "2027-04-15", jurisdiction: "US Federal", category: "tax", status: "upcoming", priority: "critical", form: "Form 1120" },
];

const statusMeta: Record<EventStatus, { label: string; color: string; bg: string; border: string; icon: React.ElementType }> = {
  completed:  { label: "Completed",  color: "#059669", bg: "#ecfdf5", border: "#a7f3d0", icon: CheckCircle2 },
  upcoming:   { label: "Upcoming",   color: "#2563eb", bg: "#eff6ff", border: "#bfdbfe", icon: Calendar },
  due_soon:   { label: "Due Soon",   color: "#d97706", bg: "#fffbeb", border: "#fde68a", icon: Clock },
  overdue:    { label: "Overdue",    color: "#dc2626", bg: "#fef2f2", border: "#fecaca", icon: AlertTriangle },
};

const priorityColors = {
  critical: "text-red-700 bg-red-50 border-red-200",
  high:     "text-amber-700 bg-amber-50 border-amber-200",
  medium:   "text-blue-700 bg-blue-50 border-blue-200",
  low:      "text-gray-600 bg-gray-50 border-gray-200",
};

const categoryIcons: Record<EventCategory, React.ElementType> = {
  tax:        DollarSign,
  payroll:    Users,
  corporate:  Building2,
  compliance: Shield,
  banking:    Globe,
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export default function CompliancePage() {
  const { openChat } = useAppStore();
  const [categoryFilter, setCategoryFilter] = useState<EventCategory | "all">("all");
  const [viewMode, setViewMode] = useState<"list" | "calendar">("list");

  const filtered = EVENTS.filter(e => categoryFilter === "all" || e.category === categoryFilter);
  const dueSoon = EVENTS.filter(e => e.status === "due_soon").length;
  const upcoming30 = EVENTS.filter(e => e.status === "upcoming" && new Date(e.due_date) <= new Date("2026-05-20")).length;
  const completed = EVENTS.filter(e => e.status === "completed").length;

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Compliance Calendar" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Shield className="h-3.5 w-3.5" /> Regulatory Intelligence
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Compliance Calendar</h1>
              <p className="mt-1 text-sm text-[#5f5344]">Tax filings, regulatory deadlines, payroll, and corporate compliance—all in one place.</p>
            </div>
            <button onClick={() => openChat("What compliance deadlines are coming up in the next 30 days and what do I need to prepare?")} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white self-start lg:self-auto">
              <Sparkles className="h-4 w-4" /> AI Deadline Brief
            </button>
          </div>
        </section>

        {/* Stats */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Due Soon (7 days)", value: dueSoon.toString(), color: dueSoon > 0 ? "text-amber-700" : "text-emerald-700" },
            { label: "Next 30 Days", value: upcoming30.toString(), color: "text-blue-700" },
            { label: "Completed (YTD)", value: completed.toString(), color: "text-emerald-700" },
            { label: "Total This Year", value: EVENTS.length.toString(), color: "text-[#2a2017]" },
          ].map(s => (
            <article key={s.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{s.label}</p>
              <p className={cn("mt-2 text-3xl font-black", s.color)}>{s.value}</p>
            </article>
          ))}
        </section>

        {/* Due Soon Banner */}
        {dueSoon > 0 && (
          <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-amber-600 shrink-0" />
              <div>
                <p className="text-sm font-bold text-amber-900">Action required: {dueSoon} deadline{dueSoon > 1 ? "s" : ""} due within 7 days</p>
                {EVENTS.filter(e => e.status === "due_soon").map(e => (
                  <p key={e.id} className="text-xs text-amber-800 mt-0.5">· {e.title} — due {e.due_date}{e.form ? ` (${e.form})` : ""}</p>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Filters + List */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between border-b border-[#ede8e0]">
            <div className="flex gap-2 flex-wrap">
              {(["all", "tax", "payroll", "corporate", "compliance", "banking"] as const).map(c => (
                <button key={c} onClick={() => setCategoryFilter(c)} className={cn("rounded-full px-3 py-1 text-xs font-semibold border capitalize transition-all", categoryFilter === c ? "bg-[#231c15] text-white border-[#231c15]" : "bg-white border-[#ddd2c2] text-[#776b5a] hover:border-[#b8a898]")}>
                  {c === "all" ? "All Categories" : c.charAt(0).toUpperCase() + c.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="divide-y divide-[#f0ebe3]">
            {filtered.map((event) => {
              const status = statusMeta[event.status];
              const StatusIcon = status.icon;
              const CatIcon = categoryIcons[event.category];
              const daysUntil = Math.ceil((new Date(event.due_date).getTime() - new Date("2026-04-20").getTime()) / (1000 * 60 * 60 * 24));
              return (
                <div key={event.id} className={cn("flex items-start gap-4 px-5 py-4 hover:bg-[#fdf9f4] transition-colors", event.status === "due_soon" && "bg-amber-50/50")}>
                  <div className="mt-0.5 p-2 rounded-xl bg-[#f0ebe3] shrink-0">
                    <CatIcon className="h-4 w-4 text-[#8d4f27]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-bold text-[#2a2017]">{event.title}</p>
                        <p className="text-xs text-[#776b5a] mt-0.5">{event.description}</p>
                        <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                          <span className="text-xs font-medium text-[#9a8872]">{event.jurisdiction}</span>
                          {event.form && <span className="text-xs bg-[#f0ebe3] text-[#6b5344] px-1.5 py-0.5 rounded font-mono">{event.form}</span>}
                          <span className={cn("text-xs font-semibold border rounded-full px-2 py-0.5", priorityColors[event.priority])}>
                            {event.priority.toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold border mb-1" style={{ color: status.color, background: status.bg, borderColor: status.border }}>
                          <StatusIcon className="h-3 w-3" /> {status.label}
                        </span>
                        <p className="text-xs text-[#776b5a]">{event.due_date}</p>
                        {event.status !== "completed" && (
                          <p className={cn("text-xs font-semibold mt-0.5", daysUntil <= 7 ? "text-amber-600" : daysUntil <= 30 ? "text-blue-600" : "text-[#9a8872]")}>
                            {daysUntil < 0 ? `${Math.abs(daysUntil)}d overdue` : daysUntil === 0 ? "Due today!" : `${daysUntil}d remaining`}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => openChat(`Help me prepare for ${event.title}. Due date: ${event.due_date}. Form: ${event.form || "N/A"}. Provide a practical checklist and owner-wise tasks.`)}
                    className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a] shrink-0"
                    title="Open compliance action brief"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              );
            })}
          </div>
        </section>

        {/* Upcoming Quarter Summary */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5 sm:p-6">
          <h2 className="text-base font-bold text-[#2a2017] mb-4">Q2 2026 Compliance Overview</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { title: "Tax Filings", count: 4, icon: DollarSign, color: "#8d4f27" },
              { title: "Payroll Deadlines", count: 6, icon: Users, color: "#2563eb" },
              { title: "Corporate Filings", count: 1, icon: Building2, color: "#059669" },
              { title: "Compliance Reviews", count: 2, icon: Shield, color: "#7c3aed" },
              { title: "Banking / FinCEN", count: 1, icon: Globe, color: "#d97706" },
              { title: "Board Requirements", count: 2, icon: FileText, color: "#6b7280" },
            ].map(item => {
              const Icon = item.icon;
              return (
                <div key={item.title} className="flex items-center gap-3 rounded-xl border border-[#ede8e0] p-4">
                  <div className="p-2 rounded-xl shrink-0" style={{ background: `${item.color}15` }}>
                    <Icon className="h-4 w-4" style={{ color: item.color }} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[#2a2017]">{item.title}</p>
                    <p className="text-xs text-[#776b5a]">{item.count} deadline{item.count !== 1 ? "s" : ""} this quarter</p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
