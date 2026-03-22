"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, Table, TableBody, TableCell, TableHead, TableHeaderCell, TableRow, Title } from "@tremor/react";
import { useFinancialData } from "@/hooks/useFinancialData";
import api from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = API_BASE.replace(/\/$/, "").endsWith("/api/v1") ? API_BASE.replace(/\/$/, "") : `${API_BASE.replace(/\/$/, "")}/api/v1`;
const formatINR = (v: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v || 0);

export default function FinanceDashboardPage() {
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
  const [companyId, setCompanyId] = useState<string>("");
  const [pendingReview, setPendingReview] = useState<Record<string, any[]>>({});
  const [reconciliation, setReconciliation] = useState<{ netBurn: number; expenseTotal: number; variance: number } | null>(null);
  const { data, isLoading } = useFinancialData(companyId, month);

  useEffect(() => {
    const load = async () => {
      const health = await api.getStartupHealth();
      const cid = health.default_company_id || "";
      setCompanyId(cid);
    };
    load();
  }, []);

  useEffect(() => {
    const loadFinance = async () => {
      if (!companyId) return;
      const [pendingRes, burnRes, expensesRes] = await Promise.all([
        fetch(`${API_V1}/inputs/pending-review?company_id=${companyId}`, { headers: { "X-User-Role": "finance" } }),
        fetch(`${API_V1}/burn/summary/${companyId}?month=${month}`),
        fetch(`${API_V1}/burn/expenses/${companyId}?month=${month}`),
      ]);

      const pending = pendingRes.ok ? await pendingRes.json() : { pending_review: {} };
      const burn = burnRes.ok ? await burnRes.json() : { net_burn: 0 };
      const expenses = expensesRes.ok ? await expensesRes.json() : { tech_costs: {}, non_tech_costs: {} };

      setPendingReview(pending.pending_review || {});

      const techTotal = Number(expenses.tech_costs?.aws_total || 0) + Number(expenses.tech_costs?.licenses_total || 0) + Number(expenses.tech_costs?.saas_total || 0);
      const nonTechTotal = Number(expenses.non_tech_costs?.marketing || 0) + Number(expenses.non_tech_costs?.office_bengaluru || 0) + Number(expenses.non_tech_costs?.office_gangavathi || 0) + Number(expenses.non_tech_costs?.misc || 0);
      const expenseTotal = techTotal + nonTechTotal;
      const netBurn = Number(burn.net_burn || 0);
      setReconciliation({ netBurn, expenseTotal, variance: netBurn - expenseTotal });
    };
    loadFinance();
  }, [companyId, month]);

  const rows = useMemo(() => {
    const summary = data?.dashboard?.summary;
    if (!summary?.breakdown_by_category) return [];
    return Object.entries(summary.breakdown_by_category).map(([category, amount]) => ({
      category,
      product: "shared",
      amount: Number(amount),
      type: "recurring",
      source: "system",
      date: `${month}-01`,
    }));
  }, [data, month]);

  return (
    <div className="min-h-screen bg-[#f6f3ee] text-[#1d1b19] p-8 space-y-6">
      <Title>Finance Team Dashboard</Title>

      <div className="flex items-center gap-3">
        <input
          type="month"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          className="bg-white border border-[#e1d3c2] rounded px-3 py-2"
        />
        <button className="px-4 py-2 rounded bg-[#9a5d34] hover:bg-[#7f4c2a] text-white text-sm font-semibold">Export</button>
      </div>

      <Card>
        <Title>Expense Breakdown</Title>
        <Table className="mt-4">
          <TableHead>
            <TableRow>
              <TableHeaderCell>Category</TableHeaderCell>
              <TableHeaderCell>Product</TableHeaderCell>
              <TableHeaderCell>Amount (INR)</TableHeaderCell>
              <TableHeaderCell>Type</TableHeaderCell>
              <TableHeaderCell>Source</TableHeaderCell>
              <TableHeaderCell>Date</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((r, idx) => (
              <TableRow key={idx}>
                <TableCell>{r.category}</TableCell>
                <TableCell>{r.product}</TableCell>
                <TableCell>{formatINR(r.amount)}</TableCell>
                <TableCell>{r.type}</TableCell>
                <TableCell>{r.source}</TableCell>
                <TableCell>{r.date}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      <Card>
        <Title>Pending Review</Title>
        <div className="mt-3 space-y-3">
          {Object.keys(pendingReview).length === 0 && <p className="text-sm text-[#6f655a]">No pending manual entries in last 7 days.</p>}
          {Object.entries(pendingReview as Record<string, any[]>).map(([role, entries]: [string, any[]]) => (
            <div key={role} className="rounded-lg border border-[#e4d8cb] bg-white/70 p-3">
              <p className="text-xs font-black uppercase tracking-[0.12em] text-[#7f6d59]">{role}</p>
              <p className="mt-1 text-sm text-[#2a231d]">{entries.length} entries</p>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <Title>Net Burn Reconciliation</Title>
        <div className="mt-3 text-sm text-[#3a3128] space-y-1">
          <p>Net burn (ledger): {formatINR(reconciliation?.netBurn || 0)}</p>
          <p>Expense total (breakdown): {formatINR(reconciliation?.expenseTotal || 0)}</p>
          <p className={Math.abs(reconciliation?.variance || 0) > 50000 ? "text-rose-700 font-semibold" : "text-emerald-700 font-semibold"}>
            Variance: {formatINR(reconciliation?.variance || 0)}
          </p>
        </div>
      </Card>

      {isLoading && <p className="text-sm text-[#7a6f62]">Loading finance data...</p>}
    </div>
  );
}
