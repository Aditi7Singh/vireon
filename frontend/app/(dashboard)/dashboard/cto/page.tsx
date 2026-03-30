"use client";

import { useEffect, useState } from "react";
import { BarChart, Card, DonutChart, Metric, Table, TableBody, TableCell, TableHead, TableHeaderCell, TableRow, Title, Badge } from "@tremor/react";
import { AlertCircle, CheckCircle2, Loader, TrendingUp } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = API_BASE.replace(/\/$/, "").endsWith("/api/v1") ? API_BASE.replace(/\/$/, "") : `${API_BASE.replace(/\/$/, "")}/api/v1`;

const formatINR = (v: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v || 0);

export default function CTODashboardPage() {
  const [companyId, setCompanyId] = useState<string>("");
  const [techData, setTechData] = useState<any>(null);
  const [recentEntries, setRecentEntries] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    cost_type: "",
    product_tag: "ai_lab",
    amount_inr: 0,
    billing_period: new Date().toISOString().slice(0, 7),
    vendor_name: "",
    description: "",
    is_recurring: false,
  });
  const [submitError, setSubmitError] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [impact, setImpact] = useState<any>(null);
  const [hiringForm, setHiringForm] = useState({ annual_ctc: 1800000 });
  const [isCalculating, setIsCalculating] = useState(false);
  const [calcError, setCalcError] = useState<string>("");

  useEffect(() => {
    const load = async () => {
      try {
        const health = await api.getStartupHealth();
        const cid = health.default_company_id || "";
        setCompanyId(cid);
        if (!cid) return;

        const historyRes = await fetch(`${API_V1}/metrics/history/${cid}?months=6`);
        const historyPayload = historyRes.ok ? await historyRes.json() : [];
        const latestMonth = historyPayload?.[historyPayload.length - 1]?.month || new Date().toISOString().slice(0, 7);
        setFormData((prev) => ({ ...prev, billing_period: latestMonth }));

        const month = latestMonth;
        const [dashboardRes, entriesRes] = await Promise.all([
          fetch(`${API_V1}/burn/dashboard/${cid}?month=${month}`),
          fetch(`${API_V1}/ledger/entries?company_id=${cid}&category=tech_cost&entry_type=debit`),
        ]);
        
        const dashboardData = dashboardRes.ok ? await dashboardRes.json() : null;
        const ledgerEntries = entriesRes.ok ? await entriesRes.json() : [];
        
        const monthList = Array.from({ length: 6 }).map((_, i) => {
          const d = new Date();
          d.setMonth(d.getMonth() - (5 - i));
          return d.toISOString().slice(0, 7);
        });

        const monthlyDashboardResults = await Promise.all(
          monthList.map(async (m) => {
            try {
              const res = await fetch(`${API_V1}/burn/dashboard/${cid}?month=${m}`);
              if (!res.ok) return { month: m, amount: 0 };
              const payload = await res.json();
              const tech = payload?.expenses?.tech_costs || {};
              const amount = Number(tech.aws_total || 0) + Number(tech.licenses_total || 0) + Number(tech.saas_total || 0);
              return { month: m, amount };
            } catch {
              return { month: m, amount: 0 };
            }
          })
        );
        
        setTechData(dashboardData);
        setRecentEntries(ledgerEntries.slice(0, 8));
        setHistory(monthlyDashboardResults);
      } catch (err) {
        console.error("Failed to load CTO data:", err);
      }
    };
    load();
  }, []);

  async function submitTechCost() {
    if (!companyId) {
      setSubmitError("Company ID not loaded");
      return;
    }
    if (!formData.cost_type) {
      setSubmitError("Please select a cost type");
      return;
    }
    if (!formData.amount_inr || formData.amount_inr <= 0) {
      setSubmitError("Amount must be greater than 0");
      return;
    }
    
    setSubmitError("");
    setIsSubmitting(true);
    try {
      const res = await fetch(`${API_V1}/inputs/tech-cost`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-User-Role": "cto" },
        body: JSON.stringify({ ...formData, company_id: companyId }),
      });
      
      if (!res.ok) {
        const payload = await res.json().catch(() => ({}));
        throw new Error(payload?.detail || `Failed to submit tech cost (${res.status})`);
      }
      
      setFormData((prev) => ({ ...prev, cost_type: "", amount_inr: 0, vendor_name: "", description: "", is_recurring: false }));

      const month = new Date().toISOString().slice(0, 7);
      const dashboardRes = await fetch(`${API_V1}/burn/dashboard/${companyId}?month=${month}`);
      if (dashboardRes.ok) {
        setTechData(await dashboardRes.json());
      }
      
      const entriesRes = await fetch(`${API_V1}/ledger/entries?company_id=${companyId}&category=tech_cost&entry_type=debit`);
      if (entriesRes.ok) {
        setRecentEntries((await entriesRes.json()).slice(0, 8));
      }
    } catch (error) {
      const msg = error instanceof Error ? error.message : "Failed to submit tech cost. Please try again.";
      setSubmitError(msg);
      console.error("Submit error:", error);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function calculateImpact() {
    setCalcError("");
    if (!companyId) {
      setCalcError("Company ID not loaded");
      return;
    }
    if (!hiringForm.annual_ctc || hiringForm.annual_ctc <= 0) {
      setCalcError("Annual CTC must be greater than 0");
      return;
    }
    
    setIsCalculating(true);
    try {
      const res = await fetch(`${API_V1}/forecast/hiring-impact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          company_id: companyId, 
          annual_ctc_inr: hiringForm.annual_ctc, 
          join_month: new Date().toISOString().slice(0, 7) 
        }),
      });
      
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.detail || `Failed to calculate impact (${res.status})`);
      }
      
      const data = await res.json();
      setImpact(data);
    } catch (error) {
      const msg = error instanceof Error ? error.message : "Failed to calculate hiring impact. Please try again.";
      setCalcError(msg);
      console.error("Impact calculation error:", error);
    } finally {
      setIsCalculating(false);
    }
  }

  const techCosts = techData?.expenses?.tech_costs || {};
  const summary = techData?.summary || {};
  const totalTechSpend = (techCosts.aws_total || 0) + (techCosts.licenses_total || 0) + (techCosts.saas_total || 0);
  const techPercentOfBurn = summary.net_burn ? ((totalTechSpend / summary.net_burn) * 100).toFixed(1) : "0.0";

  const trendData = history.length ? history : [{ month: new Date().toISOString().slice(0, 7), amount: totalTechSpend }];

  const donutData = Object.entries(techCosts.by_product || {}).map(([product, amount]) => ({ product, amount: Number(amount) }));

  function exportTechCsv() {
    const rows = [
      ["metric", "value"],
      ["total_tech_spend", totalTechSpend],
      ["aws_total", Number(techCosts.aws_total || 0)],
      ["licenses_total", Number(techCosts.licenses_total || 0)],
      ["saas_total", Number(techCosts.saas_total || 0)],
      ["tech_percent_of_burn", techPercentOfBurn],
      [],
      ["entry_description", "entry_amount_inr"],
      ...recentEntries.map((e) => [e.description || e.category || "", Number(e.amount_inr || 0)]),
    ];
    const csv = rows.map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cto-tech-summary-${companyId || "company"}-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  async function exportTechPdf() {
    if (!companyId) return;
    const res = await fetch(`${API_V1}/reports/export/summary/pdf?company_id=${companyId}`);
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cto-summary-${companyId}-${new Date().toISOString().slice(0, 10)}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="min-h-screen bg-[#f6f3ee] text-[#1d1b19] p-8 space-y-6">
      <div className="flex items-center justify-between gap-3">
        <Title>CTO Dashboard</Title>
        <div className="flex items-center gap-2">
          <button onClick={exportTechCsv} className="px-4 py-2 rounded bg-[#9a5d34] hover:bg-[#7f4c2a] text-white text-sm font-semibold">Export CSV</button>
          <button onClick={exportTechPdf} className="px-4 py-2 rounded bg-[#1f1a16] hover:bg-[#151210] text-white text-sm font-semibold">Export PDF</button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><Title>Total Tech Spend</Title><Metric>{formatINR(totalTechSpend)}</Metric></Card>
        <Card><Title>AWS Cost</Title><Metric>{formatINR(techCosts.aws_total || 0)}</Metric></Card>
        <Card><Title>Software Licenses</Title><Metric>{formatINR(techCosts.licenses_total || 0)}</Metric></Card>
        <Card><Title>Tech % of Burn</Title><Metric>{techPercentOfBurn}%</Metric></Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-[#2a2017]">Tech Cost Trend</h2>
              <p className="text-xs text-[#7e715f] mt-0.5">Last 6 months</p>
            </div>
            <TrendingUp className="h-4 w-4 text-[#9a5d34]" />
          </div>
          {trendData.length > 0 && (
            <div className="h-[250px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                  <defs>
                    <linearGradient id="techCostFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#f97316" stopOpacity={0.01} />
                    </linearGradient>
                    <filter id="shadowTechChart">
                      <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.08" />
                    </filter>
                  </defs>
                  <XAxis 
                    dataKey="month" 
                    tickLine={false} 
                    axisLine={{ stroke: "#e8dccf", strokeWidth: 1 }} 
                    tick={{ fill: "#7b6d5b", fontSize: 12, fontWeight: 500 }}
                  />
                  <YAxis 
                    tickLine={false} 
                    axisLine={{ stroke: "#e8dccf", strokeWidth: 1 }} 
                    tick={{ fill: "#7b6d5b", fontSize: 12 }}
                    tickFormatter={(v) => `₹${Math.round(v / 100000)}L`}
                  />
                  <Tooltip 
                    contentStyle={{
                      borderRadius: 12,
                      border: "1px solid #e0cfc2",
                      background: "#fffbf5",
                      boxShadow: "0 4px 12px rgba(63, 45, 24, 0.15)",
                      color: "#2a2118",
                    }}
                    formatter={(value) => [`₹${(Number(value) || 0).toLocaleString()}`, 'Tech Spend']}
                    labelFormatter={(label) => `${label} 2024`}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="amount" 
                    stroke="#ea580c" 
                    strokeWidth={2.4} 
                    fill="url(#techCostFill)"
                    filter="url(#shadowTechChart)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
          <div className="mt-4 flex items-center justify-between pt-4 border-t border-[#ede8df]">
            <span className="text-xs text-[#6f6251]">Current month: {trendData?.[trendData.length - 1]?.month || 'N/A'}</span>
            <span className="text-sm font-semibold text-[#2a2017]">₹{(trendData?.[trendData.length - 1]?.amount || 0).toLocaleString()}</span>
          </div>
        </Card>

        <Card className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 sm:p-6">
          <h2 className="text-lg font-semibold text-[#2a2017] mb-4">AWS Cost Breakdown by Product</h2>
          {donutData.length > 0 ? (
            <div className="space-y-3">
              {donutData.map((item, idx) => {
                const colors = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#0ea5e9", "#8b5cf6"];
                const color = colors[idx % colors.length];
                const totalAmount = donutData.reduce((sum, d) => sum + (Number(d.amount) || 0), 0);
                const percentage = totalAmount > 0 ? ((Number(item.amount) || 0) / totalAmount) * 100 : 0;
                return (
                  <div key={item.product} className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
                        <span className="text-sm font-medium text-[#2a2017]">{item.product}</span>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold text-[#2a2017]">₹{(Number(item.amount) || 0).toLocaleString()}</p>
                        <p className="text-xs text-[#7b6d5b]">{percentage.toFixed(1)}%</p>
                      </div>
                    </div>
                    <div className="w-full h-2 bg-[#f0ebe3] rounded-full overflow-hidden">
                      <div 
                        className="h-full rounded-full transition-all" 
                        style={{ width: `${percentage}%`, backgroundColor: color }}
                      />
                    </div>
                  </div>
                );
              })}
              <div className="pt-3 border-t border-[#ede8df] mt-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-[#6f6251]">Total AWS Cost</span>
                  <span className="text-lg font-bold text-[#2a2017]">₹{donutData.reduce((sum, d) => sum + (Number(d.amount) || 0), 0).toLocaleString()}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-[#7b6d5b]">
              <p>No AWS cost data available</p>
              <p className="text-xs mt-1">Add AWS resources to track costs</p>
            </div>
          )}
        </Card>
      </div>

      <Card className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 sm:p-6">
        <Title>Quick Entry - Tech Cost</Title>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
          <select 
            className="bg-white border border-[#e1d3c2] rounded px-3 py-2" 
            value={formData.cost_type} 
            onChange={(e) => setFormData({ ...formData, cost_type: e.target.value })}
          >
            <option value="">Select Cost Type</option>
            <option value="aws">AWS</option>
            <option value="saas">SaaS</option>
            <option value="licenses">Licenses</option>
            <option value="tools">Tools</option>
          </select>
          <input 
            className="bg-white border border-[#e1d3c2] rounded px-3 py-2" 
            value={formData.vendor_name} 
            onChange={(e) => setFormData({ ...formData, vendor_name: e.target.value })} 
            placeholder="Vendor (e.g., AWS, Slack)" 
          />
          <input 
            className="bg-white border border-[#e1d3c2] rounded px-3 py-2" 
            type="number" 
            value={formData.amount_inr} 
            onChange={(e) => setFormData({ ...formData, amount_inr: Number(e.target.value) })} 
            placeholder="Amount INR" 
          />
          <input 
            className="bg-white border border-[#e1d3c2] rounded px-3 py-2" 
            value={formData.description} 
            onChange={(e) => setFormData({ ...formData, description: e.target.value })} 
            placeholder="Description" 
          />
        </div>
        <div className="flex items-center gap-2 mt-4">
          <button 
            onClick={submitTechCost} 
            disabled={isSubmitting}
            className="px-4 py-2 rounded bg-[#9a5d34] hover:bg-[#7f4c2a] disabled:bg-[#c4a78a] text-white text-sm font-semibold flex items-center gap-2"
          >
            {isSubmitting && <Loader className="w-4 h-4 animate-spin" />}
            {isSubmitting ? "Submitting..." : "Submit Tech Cost"}
          </button>
        </div>
        
        {submitError && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-red-700">{submitError}</p>
          </div>
        )}

        <Table className="mt-6">
          <TableHead><TableRow><TableHeaderCell>Recent Entries</TableHeaderCell><TableHeaderCell>Amount</TableHeaderCell></TableRow></TableHead>
          <TableBody>
            {recentEntries.length === 0 && (
              <TableRow><TableCell>No entries loaded</TableCell><TableCell>{formatINR(0)}</TableCell></TableRow>
            )}
            {recentEntries.map((entry) => (
              <TableRow key={entry.id}>
                <TableCell>{entry.description || entry.category}</TableCell>
                <TableCell>{formatINR(Number(entry.amount_inr || 0))}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      <Card>
        <Title>Hiring Impact Calculator</Title>
        <p className="text-sm text-[#7f7770] mt-2">Estimate runway impact of adding a new hire</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
          <div>
            <label className="block text-xs font-semibold text-[#5e5243] mb-1">Annual CTC (₹)</label>
            <input 
              className="w-full bg-white border border-[#e1d3c2] rounded px-3 py-2" 
              type="number" 
              value={hiringForm.annual_ctc} 
              onChange={(e) => setHiringForm({ annual_ctc: Number(e.target.value) })} 
              placeholder="e.g., 1200000" 
            />
          </div>
        </div>
        
        <div className="flex items-center gap-2 mt-4">
          <button 
            onClick={calculateImpact} 
            disabled={isCalculating}
            className="px-4 py-2 rounded bg-[#1f1a16] hover:bg-[#151210] disabled:bg-[#7f7770] text-white text-sm font-semibold flex items-center gap-2"
          >
            {isCalculating && <Loader className="w-4 h-4 animate-spin" />}
            {isCalculating ? "Calculating..." : "Calculate Impact"}
          </button>
        </div>

        {calcError && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-red-700">{calcError}</p>
          </div>
        )}
        
        {impact && (
          <div className="mt-6 p-4 bg-[#f0ebe4] rounded border border-[#e1d3c2] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-[#5e5243]">Current Runway:</span>
              <span className="font-semibold text-[#1d1b19]">{impact.baseline_runway_months} months</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-[#5e5243]">After New Hire:</span>
              <span className="font-semibold text-[#1d1b19]">{impact.new_runway_months} months</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-[#5e5243]">Impact:</span>
              <span className={`font-semibold ${impact.runway_impact_days < 0 ? "text-red-600" : "text-green-600"}`}>
                {impact.runway_impact_days < 0 ? "−" : "+"}{Math.abs(impact.runway_impact_days)} days
              </span>
            </div>
            {impact.projected_12m_costs && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-[#5e5243]">12-Month Cost:</span>
                <span className="font-semibold text-[#1d1b19]">{formatINR(impact.projected_12m_costs)}</span>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
