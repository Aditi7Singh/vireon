"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import {
  Building2, Cloud, Scale, Megaphone, Zap, Flame,
  Sparkles, TrendingDown, AlertTriangle, CheckCircle2,
  RefreshCw, Info,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, BarChart, Bar, Cell, Legend,
} from "recharts";

const INR = (n: number) =>
  n >= 10_000_000
    ? `₹${(n / 10_000_000).toFixed(2)}Cr`
    : n >= 100_000
    ? `₹${(n / 100_000).toFixed(1)}L`
    : `₹${n.toLocaleString("en-IN")}`;

const OVERHEAD_CATEGORIES = [
  {
    id: "office",
    label: "Office & Facilities",
    icon: Building2,
    color: "#10b981",
    description: "Rent, internet, utilities — Bengaluru HQ + Gangavathi office",
    monthly_inr: 305000,
    yoy_change: 4.2,
    items: [
      { name: "Bengaluru HQ rent",        inr: 150000, vendor: "DivyaSri Properties",   notes: "12-month lease at ₹150/sqft" },
      { name: "Bengaluru internet & power",inr: 35000,  vendor: "ACT Fibernet / BESCOM", notes: "200 Mbps + UPS backup" },
      { name: "Gangavathi office rent",    inr: 80000,  vendor: "Local lease",           notes: "Field hub for Sprout team" },
      { name: "Maintenance & housekeeping",inr: 25000,  vendor: "CleanPro Services",     notes: "Monthly contract" },
      { name: "Pantry & supplies",         inr: 15000,  vendor: "Various",               notes: "Recurring estimate" },
    ],
  },
  {
    id: "infra",
    label: "Cloud & Infrastructure",
    icon: Cloud,
    color: "#6366f1",
    description: "AWS compute, storage, GPU inference, monitoring, CI/CD",
    monthly_inr: 500000,
    yoy_change: 18.3,
    items: [
      { name: "AWS EC2 / EKS compute",     inr: 165000, vendor: "Amazon Web Services",   notes: "Production + staging clusters" },
      { name: "GPU inference cluster",     inr: 200000, vendor: "AWS / Lambda Labs",     notes: "AI Lab model serving (p3 instances)" },
      { name: "S3 + RDS + CloudFront",     inr: 45000,  vendor: "Amazon Web Services",   notes: "Storage, DB & CDN" },
      { name: "Observability (Datadog)",   inr: 35000,  vendor: "Datadog",               notes: "APM + logs + dashboards" },
      { name: "CI/CD (GitHub Actions)",    inr: 25000,  vendor: "GitHub",                notes: "Enterprise plan" },
      { name: "Security (Snyk + Vault)",   inr: 30000,  vendor: "Snyk / HashiCorp",      notes: "Vuln scanning + secrets mgmt" },
    ],
  },
  {
    id: "saas",
    label: "SaaS Tools & Subscriptions",
    icon: Zap,
    color: "#f59e0b",
    description: "Productivity, communication, design, and developer tools",
    monthly_inr: 95000,
    yoy_change: 8.5,
    items: [
      { name: "Slack Pro",                 inr: 12000,  vendor: "Slack Technologies",    notes: "Team communication (18 seats)" },
      { name: "Notion Teams",              inr: 8000,   vendor: "Notion Labs",           notes: "Docs & project management" },
      { name: "Figma Organisation",        inr: 10000,  vendor: "Figma Inc.",            notes: "Design & prototyping" },
      { name: "Linear (project tracker)",  inr: 7000,   vendor: "Linear",                notes: "Engineering sprints" },
      { name: "Zoom Business",             inr: 9000,   vendor: "Zoom Video",            notes: "Video conferencing" },
      { name: "Google Workspace",          inr: 18000,  vendor: "Google",                notes: "Email + Drive + Meet (18 seats)" },
      { name: "Loom + other tools",        inr: 12000,  vendor: "Various",               notes: "Async video + misc" },
      { name: "1Password Teams",           inr: 6000,   vendor: "1Password",             notes: "Credential management" },
      { name: "HubSpot Starter",           inr: 13000,  vendor: "HubSpot",               notes: "CRM for Orchard sales" },
    ],
  },
  {
    id: "legal",
    label: "Legal & Compliance",
    icon: Scale,
    color: "#f43f5e",
    description: "Legal retainer, auditors, company secretary, regulatory filings",
    monthly_inr: 88000,
    yoy_change: 2.1,
    items: [
      { name: "Legal retainer",            inr: 40000,  vendor: "TLA & Associates",      notes: "Monthly counsel (IP + contracts)" },
      { name: "Statutory auditor",         inr: 20000,  vendor: "S.R. & Co. CA",         notes: "Paid monthly, annual audit" },
      { name: "Company secretary",         inr: 15000,  vendor: "CS Prakash Murthy",     notes: "ROC filings + minutes" },
      { name: "Regulatory & compliance",   inr: 13000,  vendor: "Various",               notes: "MCA, IT, GST compliance" },
    ],
  },
  {
    id: "marketing",
    label: "Sales & Marketing",
    icon: Megaphone,
    color: "#8b5cf6",
    description: "Paid campaigns, events, brand, and outbound for Orchard",
    monthly_inr: 120000,
    yoy_change: 22.5,
    items: [
      { name: "Google Ads (Orchard)",      inr: 50000,  vendor: "Google Ads",            notes: "B2B demand gen" },
      { name: "LinkedIn Ads",              inr: 25000,  vendor: "LinkedIn",              notes: "Enterprise ICP targeting" },
      { name: "Events & field marketing",  inr: 25000,  vendor: "Various",               notes: "AgriTech conferences" },
      { name: "Brand & content",           inr: 20000,  vendor: "In-house + freelance",  notes: "Blog, social, case studies" },
    ],
  },
];

const MONTHS = ["Nov '24", "Dec '24", "Jan '25", "Feb '25", "Mar '25", "Apr '25"];
const GROWTH_FACTORS = [0.78, 0.83, 0.88, 0.93, 0.97, 1.00];

function buildTrend() {
  return MONTHS.map((month, i) => {
    const g = GROWTH_FACTORS[i];
    const row: Record<string, number | string> = { month };
    OVERHEAD_CATEGORIES.forEach((c) => { row[c.id] = Math.round(c.monthly_inr * g); });
    return row;
  });
}

export default function OverheadPage() {
  const { openChat } = useAppStore();
  const trend = buildTrend();
  const [expanded, setExpanded] = useState<string | null>(null);

  const totalOverhead = OVERHEAD_CATEGORIES.reduce((s, c) => s + c.monthly_inr, 0);
  const annualOverhead = totalOverhead * 12;
  const highestGrowth = [...OVERHEAD_CATEGORIES].sort((a, b) => b.yoy_change - a.yoy_change)[0];

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-16 text-[#1d1b17]">
      <TopBar title="Overhead & Cost Centers" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* ── Hero ── */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.10)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Flame className="h-3.5 w-3.5" />
                Non-headcount burn analysis · FY 2025-26
              </p>
              <h1 className="mt-3 text-3xl font-bold text-[#2c2013]">Overhead & Cost Centers</h1>
              <p className="mt-1 text-sm text-[#6b5948]">
                Fixed and variable operational costs across office, infrastructure, software, and admin
              </p>

              <div className="mt-4 flex flex-wrap gap-5">
                {[
                  { label: "Monthly Overhead",  value: INR(totalOverhead),   color: "#dc2626" },
                  { label: "Annual Overhead",   value: INR(annualOverhead),  color: "#b45309" },
                  { label: "Highest Growth",    value: `${highestGrowth.label.split(" ")[0]} +${highestGrowth.yoy_change}%`,  color: "#7c3aed" },
                  { label: "Cost Categories",   value: "5 tracked",           color: "#1d4ed8" },
                ].map(({ label, value, color }) => (
                  <div key={label}>
                    <p className="text-[9px] font-black uppercase tracking-widest text-[#9c8872]">{label}</p>
                    <p className="text-base font-black" style={{ color }}>{value}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <button
                onClick={() => openChat("Identify the top 3 overhead cost-reduction opportunities without affecting engineering velocity or compliance")}
                className="inline-flex items-center gap-2 rounded-xl bg-[#1f1a16] px-4 py-2.5 text-xs font-bold text-[#fff6ea] hover:bg-[#14110f] active:scale-95 transition-all"
              >
                <Sparkles className="h-3.5 w-3.5 text-amber-300" />
                Find savings with Finley
              </button>
              <button
                onClick={() => openChat("How does our cloud spend per employee compare to Series A SaaS benchmarks?")}
                className="inline-flex items-center gap-2 rounded-xl border border-[#d9c9b4] bg-white px-4 py-2.5 text-xs font-bold text-[#5f4c38] hover:bg-[#fdf6eb] transition-all"
              >
                Benchmark cloud spend
              </button>
            </div>
          </div>
        </section>

        {/* ── Trend Chart ── */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-white p-6 shadow-[0_4px_24px_rgba(63,45,24,0.06)]">
          <p className="mb-1 text-[10px] font-black uppercase tracking-widest text-[#9c8c7c]">6-Month Overhead Trend</p>
          <h2 className="mb-4 text-base font-bold text-[#1d1b17]">Cost evolution by category</h2>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={trend} stackOffset="expand">
              <defs>
                {OVERHEAD_CATEGORIES.map((c) => (
                  <linearGradient key={c.id} id={`grad_${c.id}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={c.color} stopOpacity={0.7} />
                    <stop offset="95%" stopColor={c.color} stopOpacity={0.2} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0e8dc" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: "#9c8c7c" }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 10, fill: "#9c8c7c" }} axisLine={false} tickLine={false} />
              <Tooltip
                formatter={(val: number, name: string) => [INR(val), OVERHEAD_CATEGORIES.find((c) => c.id === name)?.label ?? name]}
                contentStyle={{ borderRadius: 12, border: "1px solid #e0d4c6", background: "#fffdf9", fontSize: 11 }}
              />
              <Legend formatter={(val) => OVERHEAD_CATEGORIES.find((c) => c.id === val)?.label ?? val} wrapperStyle={{ fontSize: 11 }} />
              {OVERHEAD_CATEGORIES.map((c) => (
                <Area key={c.id} type="monotone" dataKey={c.id} stackId="1"
                  stroke={c.color} fill={`url(#grad_${c.id})`} strokeWidth={1.5} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </section>

        {/* ── Category Cards ── */}
        <div className="space-y-4">
          {OVERHEAD_CATEGORIES.map((cat) => {
            const Icon     = cat.icon;
            const isOpen   = expanded === cat.id;
            const isGrowing = cat.yoy_change > 10;

            return (
              <div key={cat.id} className="rounded-3xl border border-[#d9cdbc] bg-white overflow-hidden shadow-[0_4px_24px_rgba(63,45,24,0.05)]">
                <button
                  onClick={() => setExpanded(isOpen ? null : cat.id)}
                  className="flex w-full items-center gap-4 px-6 py-4 text-left hover:bg-[#fdf9f4] transition-colors"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl" style={{ background: cat.color + "18" }}>
                    <Icon className="h-5 w-5" style={{ color: cat.color }} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-black text-[#1d1b17]">{cat.label}</h3>
                      {isGrowing && (
                        <span className="rounded-full bg-[#fff7ed] px-2 py-0.5 text-[9px] font-bold text-[#c2410c]">
                          +{cat.yoy_change}% YoY
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-[#8b7a69]">{cat.description}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-base font-black text-[#1d1b17]">{INR(cat.monthly_inr)}</p>
                    <p className="text-[9px] text-[#9c8c7c] uppercase tracking-wider">/ month</p>
                  </div>
                  <div className="flex items-center gap-1 text-[#b08a5c]">
                    {isGrowing ? <TrendingDown className="h-4 w-4 text-[#dc2626]" /> : <CheckCircle2 className="h-4 w-4 text-[#15803d]" />}
                  </div>
                </button>

                {/* Expanded line items */}
                {isOpen && (
                  <div className="border-t border-[#f0e8dc] bg-[#faf7f3]">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-[#ede5d9]">
                            {["Item", "Vendor", "Monthly (₹)", "Notes"].map((h) => (
                              <th key={h} className="px-5 py-2.5 text-left text-[9px] font-black uppercase tracking-widest text-[#9c8c7c]">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {cat.items.map((item, i) => (
                            <tr key={i} className="border-b border-[#f5f0eb] last:border-0 hover:bg-white/60 transition-colors">
                              <td className="px-5 py-2.5 text-xs font-semibold text-[#1d1b17]">{item.name}</td>
                              <td className="px-5 py-2.5 text-xs text-[#6b5948]">{item.vendor}</td>
                              <td className="px-5 py-2.5 text-xs font-black text-[#1d1b17]">{INR(item.inr)}</td>
                              <td className="px-5 py-2.5 text-xs text-[#9c8c7c]">{item.notes}</td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot>
                          <tr className="bg-[#f3ede6]">
                            <td colSpan={2} className="px-5 py-2 text-xs font-black text-[#1d1b17]">Subtotal</td>
                            <td className="px-5 py-2 text-xs font-black" style={{ color: cat.color }}>{INR(cat.monthly_inr)}</td>
                            <td className="px-5 py-2 text-[9px] text-[#9c8c7c]">Annual: {INR(cat.monthly_inr * 12)}</td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                    <div className="flex justify-end px-5 py-3">
                      <button
                        onClick={() => openChat(`Analyze the ${cat.label} cost line — identify waste, renegotiation opportunities, and savings vs industry benchmarks`)}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9c9b4] bg-white px-3 py-1.5 text-xs font-bold text-[#6b5948] hover:bg-[#fdf6eb] transition-all"
                      >
                        <Sparkles className="h-3 w-3 text-amber-500" />
                        Optimise with Finley
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* ── Runway impact callout ── */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(135deg,#1f1a16_0%,#2e231a_100%)] p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-black uppercase tracking-widest text-amber-400">Runway Impact</p>
              <h3 className="mt-1 text-base font-bold text-white">Overhead burns {INR(totalOverhead)}/month</h3>
              <p className="mt-1 text-xs text-[#c8b89e]">
                A 15% overhead reduction would extend runway by ~<span className="font-bold text-white">3–4 weeks</span> at current cash position.
                Finley can model exact scenarios.
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:items-end">
              {[
                "Model 20% cloud cost reduction on runway",
                "Which SaaS tools are underutilised?",
                "Negotiate office lease vs hotdesking tradeoff",
              ].map((q) => (
                <button key={q} onClick={() => openChat(q)}
                  className="rounded-xl border border-[#4a3c2e] bg-[#2e2419]/60 px-3 py-2 text-left text-xs text-[#e8d9c6] hover:bg-[#3d3025]/60 hover:text-white transition-all">
                  {q}
                </button>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
