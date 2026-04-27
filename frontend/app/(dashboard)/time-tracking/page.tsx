"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { cn } from "@/lib/utils";
import {
  Clock, Plus, Play, Square, Download, Search,
  Calendar, Users, DollarSign, TrendingUp, Sparkles,
  CheckCircle2, Circle, MoreHorizontal, X,
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";

const PROJECTS = ["Sprout", "Orchard", "AI Lab", "Internal", "Client - Acme", "Client - Nexus"];
const TEAM_MEMBERS = ["Priya Sharma", "Rahul Verma", "Ananya Iyer", "Karan Mehta", "Deepa Nair", "Aditya Kumar"];

const TIME_ENTRIES = [
  { id: "1", date: "2026-04-27", project: "Sprout", task: "Feature development - auth module", hours: 3.5, billable: true, member: "Priya Sharma", billed: false },
  { id: "2", date: "2026-04-27", project: "Orchard", task: "API design review", hours: 2.0, billable: true, member: "Rahul Verma", billed: true },
  { id: "3", date: "2026-04-27", project: "Internal", task: "Team standup & planning", hours: 1.0, billable: false, member: "Ananya Iyer", billed: false },
  { id: "4", date: "2026-04-26", project: "Client - Acme", task: "Custom dashboard delivery", hours: 4.5, billable: true, member: "Karan Mehta", billed: true },
  { id: "5", date: "2026-04-26", project: "AI Lab", task: "LangGraph agent testing", hours: 5.0, billable: false, member: "Deepa Nair", billed: false },
  { id: "6", date: "2026-04-25", project: "Sprout", task: "Bug fixes - invoicing", hours: 2.5, billable: true, member: "Aditya Kumar", billed: false },
  { id: "7", date: "2026-04-25", project: "Orchard", task: "Code review session", hours: 1.5, billable: false, member: "Priya Sharma", billed: false },
  { id: "8", date: "2026-04-24", project: "Client - Nexus", task: "Integration setup", hours: 6.0, billable: true, member: "Rahul Verma", billed: true },
];

const WEEKLY_DATA = [
  { day: "Mon", sprout: 6.5, orchard: 4, ailab: 3, client: 5 },
  { day: "Tue", sprout: 7, orchard: 3.5, ailab: 4, client: 6 },
  { day: "Wed", sprout: 5, orchard: 5, ailab: 5, client: 4 },
  { day: "Thu", sprout: 8, orchard: 2, ailab: 3, client: 7 },
  { day: "Fri", sprout: 4, orchard: 4, ailab: 6, client: 3 },
];

const PROJECT_PIE = [
  { name: "Sprout", value: 32, color: "#10b981" },
  { name: "Orchard", value: 24, color: "#f59e0b" },
  { name: "AI Lab", value: 18, color: "#8b5cf6" },
  { name: "Client - Acme", value: 14, color: "#3b82f6" },
  { name: "Client - Nexus", value: 12, color: "#ec4899" },
];

export default function TimeTrackingPage() {
  const [isTracking, setIsTracking] = useState(false);
  const [activeProject, setActiveProject] = useState("Sprout");
  const [activeTask, setActiveTask] = useState("");
  const [timer, setTimer] = useState(0);
  const [timerInterval, setTimerInterval] = useState<any>(null);
  const [search, setSearch] = useState("");
  const [showNewModal, setShowNewModal] = useState(false);

  const handleStartStop = () => {
    if (isTracking) {
      clearInterval(timerInterval);
      setIsTracking(false);
      setTimer(0);
    } else {
      setIsTracking(true);
      const interval = setInterval(() => setTimer(t => t + 1), 1000);
      setTimerInterval(interval);
    }
  };

  const formatTimer = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
  };

  const totalHours = TIME_ENTRIES.reduce((s, e) => s + e.hours, 0);
  const billableHours = TIME_ENTRIES.filter(e => e.billable).reduce((s, e) => s + e.hours, 0);
  const billedHours = TIME_ENTRIES.filter(e => e.billed).reduce((s, e) => s + e.hours, 0);

  const filtered = TIME_ENTRIES.filter(e =>
    e.project.toLowerCase().includes(search.toLowerCase()) ||
    e.task.toLowerCase().includes(search.toLowerCase()) ||
    e.member.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Time Tracking" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* Hero */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Clock className="h-3.5 w-3.5" /> Time & Billing
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Time Tracking</h1>
              <p className="mt-1 text-sm text-[#5f5344]">Track billable hours, allocate time to projects, and generate client invoices automatically.</p>
            </div>
            <div className="flex items-center gap-3">
              <button className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <Download className="h-4 w-4" /> Export Timesheet
              </button>
              <button onClick={() => setShowNewModal(true)} className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                <Plus className="h-4 w-4" /> Log Time
              </button>
            </div>
          </div>
        </section>

        {/* Live Timer */}
        <section className={cn("rounded-2xl border p-6 transition-all", isTracking ? "border-emerald-300 bg-emerald-50" : "border-[#ddd2c2] bg-[#fffdf8]")}>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="flex-1 space-y-3">
              <div className="flex items-center gap-2">
                {isTracking && <span className="flex h-2.5 w-2.5 relative"><span className="animate-ping absolute h-full w-full rounded-full bg-emerald-400 opacity-75" /><span className="relative rounded-full h-2.5 w-2.5 bg-emerald-500" /></span>}
                <p className="text-sm font-bold text-[#2a2017]">{isTracking ? "Recording time..." : "Start tracking"}</p>
              </div>
              <div className="flex flex-col sm:flex-row gap-3">
                <select value={activeProject} onChange={e => setActiveProject(e.target.value)} className="rounded-xl border border-[#ddd2c2] bg-white px-3 py-2 text-sm outline-none">
                  {PROJECTS.map(p => <option key={p}>{p}</option>)}
                </select>
                <input value={activeTask} onChange={e => setActiveTask(e.target.value)} placeholder="What are you working on?" className="flex-1 rounded-xl border border-[#ddd2c2] bg-white px-3 py-2 text-sm outline-none" />
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className={cn("text-3xl font-black font-mono", isTracking ? "text-emerald-700" : "text-[#2a2017]")}>
                {formatTimer(timer)}
              </span>
              <button onClick={handleStartStop} className={cn("w-12 h-12 rounded-full flex items-center justify-center transition-all shadow-lg",
                isTracking ? "bg-red-500 hover:bg-red-600" : "bg-emerald-500 hover:bg-emerald-600"
              )}>
                {isTracking ? <Square className="h-5 w-5 text-white" /> : <Play className="h-5 w-5 text-white" />}
              </button>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="grid gap-4 sm:grid-cols-4">
          {[
            { label: "Total Hours (Apr)", value: `${totalHours}h`, sub: "All projects", color: "text-[#2a2017]" },
            { label: "Billable Hours", value: `${billableHours}h`, sub: `${((billableHours/totalHours)*100).toFixed(0)}% of total`, color: "text-emerald-700" },
            { label: "Billed to Clients", value: `${billedHours}h`, sub: "₹" + (billedHours * 3000).toLocaleString(), color: "text-blue-700" },
            { label: "Billable Rate", value: "₹3,000/hr", sub: "Avg across team", color: "text-[#8d4f27]" },
          ].map((s) => (
            <article key={s.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{s.label}</p>
              <p className={cn("mt-2 text-2xl font-bold", s.color)}>{s.value}</p>
              <p className="mt-1 text-xs text-[#9a8872]">{s.sub}</p>
            </article>
          ))}
        </section>

        {/* Charts */}
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="lg:col-span-3 rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
            <h2 className="text-sm font-bold text-[#2a2017] mb-4">This Week — Hours by Project</h2>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={WEEKLY_DATA}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0e8de" />
                <XAxis dataKey="day" tick={{ fontSize: 11, fill: "#776b5a" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#776b5a" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ border: "1px solid #e3d6c7", borderRadius: 12, background: "#fffdf8", fontSize: 11 }} />
                <Bar dataKey="sprout" name="Sprout" fill="#10b981" radius={[3, 3, 0, 0]} stackId="a" />
                <Bar dataKey="orchard" name="Orchard" fill="#f59e0b" radius={[3, 3, 0, 0]} stackId="a" />
                <Bar dataKey="ailab" name="AI Lab" fill="#8b5cf6" radius={[3, 3, 0, 0]} stackId="a" />
                <Bar dataKey="client" name="Client" fill="#3b82f6" radius={[3, 3, 0, 0]} stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="lg:col-span-2 rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
            <h2 className="text-sm font-bold text-[#2a2017] mb-4">Time Split by Project</h2>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={PROJECT_PIE} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value">
                  {PROJECT_PIE.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip formatter={(v: number) => [`${v}h`, ""]} contentStyle={{ borderRadius: 12, fontSize: 11 }} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Time Entries Table */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="flex items-center justify-between p-5 border-b border-[#ede8e0]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9a8872]" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search time entries..." className="rounded-xl border border-[#ddd2c2] bg-[#f9f6f1] py-2 pl-9 pr-4 text-sm w-60 outline-none" />
            </div>
            <p className="text-xs text-[#9a8872]">Week of Apr 21–27, 2026</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#f9f5ef] text-[#776b5a]">
                <tr>
                  {["Date", "Team Member", "Project", "Task", "Hours", "Billable", "Actions"].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-bold uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0ebe3]">
                {filtered.map(entry => (
                  <tr key={entry.id} className="hover:bg-[#fdf9f4] transition-colors">
                    <td className="px-5 py-3.5 text-xs text-[#5f5344]">{entry.date}</td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-md bg-gradient-to-br from-[#d97706] to-[#b45309] flex items-center justify-center text-white text-[9px] font-black">
                          {entry.member.split(" ").map(n => n[0]).join("")}
                        </div>
                        <span className="text-xs text-[#2a2017]">{entry.member}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="px-2 py-0.5 bg-[#f0e8dc] text-[#6b4c1e] rounded-md text-xs font-semibold">{entry.project}</span>
                    </td>
                    <td className="px-5 py-3.5 text-[#2a2017] text-xs max-w-[200px] truncate">{entry.task}</td>
                    <td className="px-5 py-3.5 font-bold text-[#2a2017]">{entry.hours}h</td>
                    <td className="px-5 py-3.5">
                      {entry.billable ? (
                        <span className={cn("text-xs font-semibold", entry.billed ? "text-emerald-700" : "text-blue-600")}>
                          {entry.billed ? "✓ Billed" : "Billable"}
                        </span>
                      ) : (
                        <span className="text-xs text-[#9a8872]">Non-billable</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      <button className="p-1.5 rounded-lg hover:bg-[#f0ebe3] text-[#776b5a]"><MoreHorizontal className="h-4 w-4" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      {/* New Log Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b border-[#ede8e0]">
              <h2 className="text-lg font-bold text-[#2a2017]">Log Time Entry</h2>
              <button onClick={() => setShowNewModal(false)} className="p-2 rounded-lg hover:bg-[#f0ebe3]"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Date</label>
                  <input type="date" defaultValue="2026-04-27" className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Hours</label>
                  <input type="number" step="0.5" min="0.5" max="24" className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none" placeholder="e.g. 2.5" />
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Project</label>
                <select className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none">
                  {PROJECTS.map(p => <option key={p}>{p}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-[#776b5a] uppercase tracking-wide">Task Description</label>
                <input className="mt-1.5 w-full rounded-xl border border-[#ddd2c2] bg-[#faf7f3] px-3 py-2.5 text-sm outline-none" placeholder="What did you work on?" />
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="billable" defaultChecked className="rounded" />
                <label htmlFor="billable" className="text-sm text-[#2a2017] font-medium">Mark as billable</label>
              </div>
              <div className="flex gap-3 pt-2">
                <button onClick={() => setShowNewModal(false)} className="flex-1 rounded-xl border border-[#ddd2c2] py-2.5 text-sm font-medium text-[#776b5a] hover:bg-[#f5f0ea]">Cancel</button>
                <button onClick={() => setShowNewModal(false)} className="flex-1 rounded-xl bg-[#231c15] py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">Save Entry</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
