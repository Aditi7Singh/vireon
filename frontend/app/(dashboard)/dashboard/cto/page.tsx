"use client";

import { useEffect, useState } from "react";
import { BarChart, Card, DonutChart, Metric, Table, TableBody, TableCell, TableHead, TableHeaderCell, TableRow, Title } from "@tremor/react";
import api from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = API_BASE.replace(/\/$/, "").endsWith("/api/v1") ? API_BASE.replace(/\/$/, "") : `${API_BASE.replace(/\/$/, "")}/api/v1`;

const formatINR = (v: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v || 0);

export default function CTODashboardPage() {
  const [companyId, setCompanyId] = useState<string>("");
  const [techData, setTechData] = useState<any>(null);
  const [recentEntries, setRecentEntries] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [form, setForm] = useState({
    cost_type: "saas_tool",
    product_tag: "ai_lab",
    amount_inr: 18000,
    billing_period: new Date().toISOString().slice(0, 7),
    vendor_name: "Anthropic Claude",
    description: "Claude subscription",
    is_recurring: true,
  });
  const [submitState, setSubmitState] = useState<string>("");
  const [impact, setImpact] = useState<any>(null);

  useEffect(() => {
    const load = async () => {
      const health = await api.getStartupHealth();
      const cid = health.default_company_id || "";
      setCompanyId(cid);
      if (!cid) return;

      const month = new Date().toISOString().slice(0, 7);
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
          const res = await fetch(`${API_V1}/burn/dashboard/${cid}?month=${m}`);
          if (!res.ok) return { month: m, amount: 0 };
          const payload = await res.json();
          const tech = payload?.expenses?.tech_costs || {};
          const amount = Number(tech.aws_total || 0) + Number(tech.licenses_total || 0) + Number(tech.saas_total || 0);
          return { month: m, amount };
        })
      );
      
      setTechData(dashboardData);
      setRecentEntries(ledgerEntries.slice(0, 8));
      setHistory(monthlyDashboardResults);
    };
    load();
  }, []);

  async function submitTechCost() {
    if (!companyId) return;
    setSubmitState("");
    const res = await fetch(`${API_V1}/inputs/tech-cost`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-User-Role": "cto" },
      body: JSON.stringify({ ...form, company_id: companyId }),
    });
    if (!res.ok) {
      const payload = await res.json().catch(() => ({}));
      setSubmitState(payload?.detail || `Failed to submit tech cost (${res.status})`);
      return;
    }
    setSubmitState("Tech cost submitted successfully.");

    const month = new Date().toISOString().slice(0, 7);
    const dashboardRes = await fetch(`${API_V1}/burn/dashboard/${companyId}?month=${month}`);
    if (dashboardRes.ok) {
      setTechData(await dashboardRes.json());
    }
  }

  async function calculateImpact() {
    if (!companyId) return;
    const res = await fetch(`${API_V1}/forecast/hiring-impact`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_id: companyId, annual_ctc_inr: 1800000, join_month: new Date().toISOString().slice(0, 7) }),
    });
    setImpact(await res.json());
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
        <Card>
          <Title>AWS Cost Breakdown by Product</Title>
          <DonutChart data={donutData.length ? donutData : [{ product: "unallocated", amount: 0 }]} category="amount" index="product" className="mt-4 h-64" />
        </Card>
        <Card>
          <Title>Tech Cost Trend</Title>
          <BarChart data={trendData} index="month" categories={["amount"]} className="mt-4 h-64" />
        </Card>
      </div>

      <Card>
        <Title>Quick Entry - Tech Cost</Title>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
          <input className="bg-white border border-[#e1d3c2] rounded px-3 py-2" value={form.vendor_name} onChange={(e) => setForm({ ...form, vendor_name: e.target.value })} placeholder="Vendor" />
          <input className="bg-white border border-[#e1d3c2] rounded px-3 py-2" type="number" value={form.amount_inr} onChange={(e) => setForm({ ...form, amount_inr: Number(e.target.value) })} placeholder="Amount INR" />
          <input className="bg-white border border-[#e1d3c2] rounded px-3 py-2" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Description" />
        </div>
        <button onClick={submitTechCost} className="mt-4 px-4 py-2 rounded bg-[#9a5d34] hover:bg-[#7f4c2a] text-white text-sm font-semibold">Submit Tech Cost</button>
        {submitState && <p className="mt-3 text-sm text-[#5e5243]">{submitState}</p>}

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
        <button onClick={calculateImpact} className="mt-4 px-4 py-2 rounded bg-[#1f1a16] hover:bg-[#151210] text-white text-sm font-semibold">Calculate Impact</button>
        {impact && (
          <p className="mt-3 text-sm">
            Current runway: {impact.baseline_runway_months} months - After hire: {impact.new_runway_months} months ({impact.runway_impact_days} days impact)
          </p>
        )}
      </Card>
    </div>
  );
}
