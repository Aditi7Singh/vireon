"use client";

import { useEffect, useMemo, useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import {
  Users, DollarSign, TrendingUp, Briefcase, MapPin,
  Sparkles, RefreshCw, Search, ChevronDown,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Cell, PieChart, Pie, Legend,
} from "recharts";

const INR = (n: number) =>
  n >= 10_000_000
    ? `₹${(n / 10_000_000).toFixed(2)}Cr`
    : n >= 100_000
    ? `₹${(n / 100_000).toFixed(1)}L`
    : `₹${n.toLocaleString("en-IN")}`;

// Static roster derived from bootstrap — shown directly for presentation
const ROSTER = [
  { id: "EMP-001", name: "Aditi Singh",     title: "Chief Executive Officer",       dept: "Leadership",   project: "Shared",   location: "Bengaluru",  salary: 420000, status: "active" },
  { id: "EMP-002", name: "Ravi Kumar",      title: "Head of Finance (CFO)",         dept: "Finance",      project: "Shared",   location: "Bengaluru",  salary: 280000, status: "active" },
  { id: "EMP-003", name: "Nina Roy",        title: "VP Operations",                 dept: "Operations",   project: "Shared",   location: "Bengaluru",  salary: 260000, status: "active" },
  { id: "EMP-004", name: "Karan Patil",     title: "Sprout Tech Lead",              dept: "Engineering",  project: "Sprout",   location: "Gangavathi", salary: 230000, status: "active" },
  { id: "EMP-005", name: "Priya Reddy",     title: "ML Engineer – Sprout",          dept: "Engineering",  project: "Sprout",   location: "Gangavathi", salary: 210000, status: "active" },
  { id: "EMP-006", name: "Sanjay Nair",     title: "Backend Engineer – Sprout",     dept: "Engineering",  project: "Sprout",   location: "Gangavathi", salary: 195000, status: "active" },
  { id: "EMP-007", name: "Meena Iyer",      title: "Product Manager – Sprout",      dept: "Product",      project: "Sprout",   location: "Gangavathi", salary: 220000, status: "active" },
  { id: "EMP-008", name: "Arjun Das",       title: "Field IoT Engineer",            dept: "Engineering",  project: "Sprout",   location: "Gangavathi", salary: 180000, status: "active" },
  { id: "EMP-009", name: "Sam Jain",        title: "Orchard Lead Engineer",         dept: "Engineering",  project: "Orchard",  location: "Bengaluru",  salary: 240000, status: "active" },
  { id: "EMP-010", name: "Ananya Krishnan", title: "Senior Backend Engineer",       dept: "Engineering",  project: "Orchard",  location: "Bengaluru",  salary: 215000, status: "active" },
  { id: "EMP-011", name: "Vikram Sharma",   title: "Enterprise Sales Manager",      dept: "Sales",        project: "Orchard",  location: "Bengaluru",  salary: 235000, status: "active" },
  { id: "EMP-012", name: "Pooja Mehta",     title: "Frontend Engineer",             dept: "Engineering",  project: "Orchard",  location: "Bengaluru",  salary: 190000, status: "active" },
  { id: "EMP-013", name: "Rahul Gupta",     title: "DevOps Engineer",               dept: "Engineering",  project: "Orchard",  location: "Bengaluru",  salary: 200000, status: "active" },
  { id: "EMP-014", name: "Divya Pillai",    title: "UX / Product Designer",         dept: "Product",      project: "Orchard",  location: "Bengaluru",  salary: 185000, status: "active" },
  { id: "EMP-015", name: "Ira Menon",       title: "AI Research Lead",              dept: "AI Research",  project: "AI Lab",   location: "Remote",     salary: 290000, status: "active" },
  { id: "EMP-016", name: "Zara Ahmed",      title: "ML Researcher – NLP",           dept: "AI Research",  project: "AI Lab",   location: "Remote",     salary: 260000, status: "active" },
  { id: "EMP-017", name: "Neel Kapoor",     title: "ML Researcher – Vision",        dept: "AI Research",  project: "AI Lab",   location: "Remote",     salary: 255000, status: "active" },
  { id: "EMP-018", name: "Tanu Bose",       title: "Data Engineer – AI Lab",        dept: "Platform",     project: "AI Lab",   location: "Remote",     salary: 210000, status: "active" },
];

const PROJECT_COLORS: Record<string, string> = {
  Sprout: "#16a34a", Orchard: "#ea580c", "AI Lab": "#7c3aed", Shared: "#6b7280",
};

const DEPT_COLORS = ["#f59e0b", "#6366f1", "#10b981", "#f43f5e", "#8b5cf6", "#0ea5e9", "#ec4899", "#14b8a6"];

function initials(name: string) {
  return name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase();
}

function salaryBand(s: number) {
  if (s >= 350000) return { label: "L6 · Senior Leadership", bg: "#fef3c7", text: "#92400e" };
  if (s >= 250000) return { label: "L5 · Principal",         bg: "#ede9fe", text: "#5b21b6" };
  if (s >= 200000) return { label: "L4 · Senior",            bg: "#dbeafe", text: "#1e40af" };
  if (s >= 150000) return { label: "L3 · Mid-level",         bg: "#dcfce7", text: "#15803d" };
  return                    { label: "L2 · Junior",           bg: "#f0fdf4", text: "#166534" };
}

export default function TeamPage() {
  const { openChat } = useAppStore();
  const [search, setSearch] = useState("");
  const [filterProject, setFilterProject] = useState("All");
  const [filterDept, setFilterDept] = useState("All");
  const [sortBy, setSortBy] = useState<"name" | "salary" | "dept">("name");

  const totalPayroll   = ROSTER.reduce((s, e) => s + e.salary, 0);
  const avgSalary      = Math.round(totalPayroll / ROSTER.length);
  const annualPayroll  = totalPayroll * 12;

  const projects = ["All", ...Array.from(new Set(ROSTER.map((e) => e.project)))];
  const depts    = ["All", ...Array.from(new Set(ROSTER.map((e) => e.dept))).sort()];

  const filtered = useMemo(() => {
    return ROSTER
      .filter((e) => {
        const q = search.toLowerCase();
        return (
          (filterProject === "All" || e.project === filterProject) &&
          (filterDept === "All" || e.dept === filterDept) &&
          (!q || e.name.toLowerCase().includes(q) || e.title.toLowerCase().includes(q))
        );
      })
      .sort((a, b) => {
        if (sortBy === "salary") return b.salary - a.salary;
        if (sortBy === "dept")   return a.dept.localeCompare(b.dept);
        return a.name.localeCompare(b.name);
      });
  }, [search, filterProject, filterDept, sortBy]);

  // Dept salary chart
  const deptChart = useMemo(() => {
    const map: Record<string, number> = {};
    ROSTER.forEach((e) => { map[e.dept] = (map[e.dept] || 0) + e.salary; });
    return Object.entries(map)
      .map(([dept, total]) => ({ dept, total, count: ROSTER.filter((e) => e.dept === dept).length }))
      .sort((a, b) => b.total - a.total);
  }, []);

  // Project headcount pie
  const projectPie = useMemo(() => {
    const map: Record<string, number> = {};
    ROSTER.forEach((e) => { map[e.project] = (map[e.project] || 0) + 1; });
    return Object.entries(map).map(([name, value]) => ({ name, value }));
  }, []);

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-16 text-[#1d1b17]">
      <TopBar title="Team & HR" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* ── Hero ── */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.10)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Users className="h-3.5 w-3.5" />
                People & Compensation · Vireon Seeding Lab
              </p>
              <h1 className="mt-3 text-3xl font-bold text-[#2c2013]">Team Directory</h1>
              <p className="mt-1 text-sm text-[#6b5948]">Full roster across Sprout, Orchard and AI Lab with salary, department, and project allocation</p>

              <div className="mt-4 flex flex-wrap gap-5">
                {[
                  { label: "Total Headcount",   value: String(ROSTER.length),   icon: Users,       color: "#1d4ed8" },
                  { label: "Monthly Payroll",   value: INR(totalPayroll),        icon: DollarSign,  color: "#dc2626" },
                  { label: "Annual Payroll",    value: INR(annualPayroll),       icon: TrendingUp,  color: "#b45309" },
                  { label: "Avg Monthly CTC",   value: INR(avgSalary),           icon: Briefcase,   color: "#6d28d9" },
                ].map(({ label, value, icon: Icon, color }) => (
                  <div key={label} className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl" style={{ background: color + "18" }}>
                      <Icon className="h-4 w-4" style={{ color }} />
                    </div>
                    <div>
                      <p className="text-[9px] font-black uppercase tracking-widest text-[#9c8872]">{label}</p>
                      <p className="text-base font-black text-[#1d1b17]">{value}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <button
              onClick={() => openChat("Analyze our payroll structure — salary distribution by department, project allocation, and recommendations to optimise people costs")}
              className="inline-flex items-center gap-2 self-start rounded-xl bg-[#1f1a16] px-4 py-2.5 text-xs font-bold text-[#fff6ea] hover:bg-[#14110f] active:scale-95 transition-all"
            >
              <Sparkles className="h-3.5 w-3.5 text-amber-300" />
              Ask Finley about payroll
            </button>
          </div>
        </section>

        {/* ── Charts row ── */}
        <div className="grid gap-5 lg:grid-cols-2">
          {/* Dept salary bar */}
          <div className="rounded-3xl border border-[#d9cdbc] bg-white p-5 shadow-[0_4px_24px_rgba(63,45,24,0.06)]">
            <p className="mb-3 text-[10px] font-black uppercase tracking-widest text-[#9c8c7c]">Monthly Payroll by Department</p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={deptChart} layout="vertical" barSize={16}>
                <XAxis type="number" tickFormatter={(v) => `₹${(v / 100000).toFixed(0)}L`} tick={{ fontSize: 9, fill: "#9c8c7c" }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="dept" tick={{ fontSize: 10, fill: "#6b5948" }} axisLine={false} tickLine={false} width={90} />
                <Tooltip formatter={(v: number) => [INR(v), "Monthly Payroll"]} contentStyle={{ borderRadius: 10, border: "1px solid #e0d4c6", fontSize: 11 }} />
                <Bar dataKey="total" radius={[0, 6, 6, 0]}>
                  {deptChart.map((_, i) => <Cell key={i} fill={DEPT_COLORS[i % DEPT_COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Project headcount pie */}
          <div className="rounded-3xl border border-[#d9cdbc] bg-white p-5 shadow-[0_4px_24px_rgba(63,45,24,0.06)]">
            <p className="mb-3 text-[10px] font-black uppercase tracking-widest text-[#9c8c7c]">Headcount by Project</p>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={projectPie} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`} labelLine={{ stroke: "#d4c4b0" }} fontSize={10}>
                  {projectPie.map((entry, i) => (
                    <Cell key={i} fill={PROJECT_COLORS[entry.name] ?? "#b08a5c"} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #e0d4c6", fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* ── Filters & Table ── */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-white shadow-[0_4px_24px_rgba(63,45,24,0.06)] overflow-hidden">
          {/* Filter bar */}
          <div className="flex flex-wrap items-center gap-3 border-b border-[#f0e8dc] p-4">
            <div className="relative flex-1 min-w-[180px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#9c8c7c]" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name or title…"
                className="w-full rounded-xl border border-[#e0d4c6] bg-[#faf7f3] pl-9 pr-3 py-2 text-xs outline-none focus:ring-2 focus:ring-[#b66b2f]/20"
              />
            </div>
            <select value={filterProject} onChange={(e) => setFilterProject(e.target.value)}
              className="rounded-xl border border-[#e0d4c6] bg-[#faf7f3] px-3 py-2 text-xs outline-none">
              {projects.map((p) => <option key={p}>{p}</option>)}
            </select>
            <select value={filterDept} onChange={(e) => setFilterDept(e.target.value)}
              className="rounded-xl border border-[#e0d4c6] bg-[#faf7f3] px-3 py-2 text-xs outline-none">
              {depts.map((d) => <option key={d}>{d}</option>)}
            </select>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value as "name" | "salary" | "dept")}
              className="rounded-xl border border-[#e0d4c6] bg-[#faf7f3] px-3 py-2 text-xs outline-none">
              <option value="name">Sort: Name</option>
              <option value="salary">Sort: Salary ↓</option>
              <option value="dept">Sort: Department</option>
            </select>
            <span className="ml-auto text-xs text-[#9c8c7c] font-semibold">{filtered.length} employees</span>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-[#f0e8dc] bg-[#faf7f3]">
                  {["Employee", "Role", "Department", "Project", "Location", "Monthly CTC", "Band"].map((h) => (
                    <th key={h} className="px-4 py-3 text-[9px] font-black uppercase tracking-widest text-[#9c8c7c] whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((e, i) => {
                  const band       = salaryBand(e.salary);
                  const projColor  = PROJECT_COLORS[e.project] ?? "#6b7280";
                  return (
                    <tr key={e.id} className={`border-b border-[#f7f3ef] hover:bg-[#fdf9f4] transition-colors ${i % 2 === 0 ? "" : "bg-[#fdfaf7]"}`}>
                      {/* Employee */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-[#3d2e1e] to-[#5c4230] text-[10px] font-black text-[#fff7ef] shadow">
                            {initials(e.name)}
                          </div>
                          <div>
                            <p className="text-xs font-bold text-[#1d1b17]">{e.name}</p>
                            <p className="text-[9px] text-[#9c8c7c]">{e.id}</p>
                          </div>
                        </div>
                      </td>
                      {/* Role */}
                      <td className="px-4 py-3">
                        <p className="text-xs text-[#3d3429] max-w-[180px] truncate">{e.title}</p>
                      </td>
                      {/* Dept */}
                      <td className="px-4 py-3">
                        <span className="rounded-lg bg-[#f3ede6] px-2 py-0.5 text-[10px] font-bold text-[#6b5948]">{e.dept}</span>
                      </td>
                      {/* Project */}
                      <td className="px-4 py-3">
                        <span className="rounded-lg px-2 py-0.5 text-[10px] font-bold"
                          style={{ background: projColor + "18", color: projColor }}>
                          {e.project}
                        </span>
                      </td>
                      {/* Location */}
                      <td className="px-4 py-3">
                        <p className="flex items-center gap-1 text-xs text-[#6b5948]">
                          <MapPin className="h-3 w-3 text-[#b08a5c]" />
                          {e.location}
                        </p>
                      </td>
                      {/* Salary */}
                      <td className="px-4 py-3">
                        <p className="text-xs font-black text-[#1d1b17]">{INR(e.salary)}</p>
                        <p className="text-[9px] text-[#9c8c7c]">{INR(e.salary * 12)} / yr</p>
                      </td>
                      {/* Band */}
                      <td className="px-4 py-3">
                        <span className="rounded-lg px-2 py-0.5 text-[9px] font-bold whitespace-nowrap"
                          style={{ background: band.bg, color: band.text }}>
                          {band.label}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Footer summary */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-t border-[#f0e8dc] bg-[#faf7f3] px-4 py-3">
            <p className="text-xs text-[#8b7a69]">
              Showing {filtered.length} of {ROSTER.length} employees ·
              Monthly payroll for selection: <span className="font-black text-[#1d1b17]">{INR(filtered.reduce((s, e) => s + e.salary, 0))}</span>
            </p>
            <button
              onClick={() => openChat("What is our total compensation liability, and how does it compare to industry benchmarks for Series A agritech companies?")}
              className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9c9b4] bg-white px-3 py-1.5 text-xs font-bold text-[#6b5948] hover:bg-[#fdf6eb] transition-all"
            >
              <Sparkles className="h-3 w-3 text-amber-500" />
              Benchmark with Finley
            </button>
          </div>
        </section>

        {/* ── India Payroll Compliance card ── */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-[#fef3c7]">
              <Briefcase className="h-5 w-5 text-[#b45309]" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-black text-[#1d1b17]">India Payroll Compliance (FY 2025-26)</h3>
              <p className="mt-1 text-xs text-[#6b5948]">All deductions computed per current Indian statutory rules</p>
              <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
                {[
                  { label: "PF (Employee)",    value: "12% of Basic",  note: "EPF Act 1952" },
                  { label: "PF (Employer)",    value: "12% of Basic",  note: "Matched contribution" },
                  { label: "Professional Tax", value: "₹200 / month",  note: "Karnataka rate" },
                  { label: "TDS (avg rate)",   value: "~10–20%",       note: "Slab-based FY26" },
                ].map(({ label, value, note }) => (
                  <div key={label} className="rounded-2xl bg-white/80 border border-[#ede5d9] px-3 py-2.5">
                    <p className="text-[9px] font-black uppercase tracking-widest text-[#9c8c7c]">{label}</p>
                    <p className="text-sm font-black text-[#1d1b17]">{value}</p>
                    <p className="text-[9px] text-[#b08a5c]">{note}</p>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-[10px] text-[#9c8c7c]">
                Total employer PF contribution this month: <span className="font-black text-[#1d1b17]">{INR(Math.round(totalPayroll * 0.12))}</span> ·
                Est. annual statutory liability: <span className="font-black text-[#1d1b17]">{INR(Math.round(totalPayroll * 0.24 * 12))}</span>
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
