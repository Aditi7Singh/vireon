"use client";

import { useEffect, useState } from "react";
import {
  AreaChart,
  Badge,
  BarChart,
  Card,
  Metric,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  Title,
} from "@tremor/react";
import { useFinancialData } from "@/hooks/useFinancialData";
import api from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = API_BASE.replace(/\/$/, "").endsWith("/api/v1")
  ? API_BASE.replace(/\/$/, "")
  : `${API_BASE.replace(/\/$/, "")}/api/v1`;

const formatINR = (v: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v || 0);

export default function CEODashboardPage() {
  const [companyId, setCompanyId] = useState<string>("");
  const [selectedMonth, setSelectedMonth] = useState<string>(new Date().toISOString().slice(0, 7));
  const [history, setHistory] = useState<any[]>([]);

  const { data, isLoading } = useFinancialData(companyId, selectedMonth);

  useEffect(() => {
    const loadCompany = async () => {
      const health = await api.getStartupHealth();
      setCompanyId(health.default_company_id || "");
    };
    loadCompany();
  }, []);

  useEffect(() => {
    const loadHistory = async () => {
      if (!companyId) return;
      const res = await fetch(`${API_V1}/metrics/history/${companyId}?months=6`);
      const payload = res.ok ? await res.json() : [];
      setHistory(payload);
    };
    loadHistory();
  }, [companyId]);

  const summary = data?.dashboard?.summary || {};
  const products = data?.dashboard?.products || {};
  const recommendations = data?.recommendations?.recommendations || [];
  const alerts = data?.alerts || [];

  const handleExportCsv = () => {
    if (!companyId) return;
    window.location.href = `${API_V1}/reports/export/ledger/csv?company_id=${companyId}`;
  };

  const handleExportPdf = () => {
    if (!companyId) return;
    window.location.href = `${API_V1}/reports/export/summary/pdf?company_id=${companyId}`;
  };

  return (
    <div className="min-h-screen bg-[#f6f3ee] text-[#1d1b19] p-8 space-y-6">
      <div className="flex items-center justify-between gap-3">
        <Title>CEO Dashboard ({selectedMonth})</Title>
        <div className="flex items-center gap-2">
          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="bg-white border border-[#e1d3c2] rounded px-3 py-2 text-sm"
          />
          <button onClick={handleExportCsv} className="px-4 py-2 rounded bg-[#9a5d34] hover:bg-[#7f4c2a] text-white text-sm font-semibold">
            Export CSV
          </button>
          <button onClick={handleExportPdf} className="px-4 py-2 rounded bg-[#1f1a16] hover:bg-[#151210] text-white text-sm font-semibold">
            Export PDF
          </button>
        </div>
      </div>

      {alerts.length > 0 && (
        <div className="rounded-xl border border-rose-300 bg-rose-50 px-4 py-3">
          <p className="text-sm font-semibold text-rose-700">Runway alert active: {alerts[0]?.runway_months} months remaining.</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-white border-[#e4d8cb]"><Title className="text-[#6f655a]">Runway</Title><Metric>{summary?.net_burn ? `${(summary.net_burn / 100000).toFixed(1)} mo` : "-"}</Metric></Card>
        <Card className="bg-white border-[#e4d8cb]"><Title className="text-[#6f655a]">Net Burn</Title><Metric>{formatINR(summary?.net_burn || 0)}</Metric></Card>
        <Card className="bg-white border-[#e4d8cb]"><Title className="text-[#6f655a]">Burn Multiple</Title><Metric>{data?.dashboard?.multiple?.burn_multiple?.toFixed?.(2) || "0.00"}x</Metric></Card>
        <Card className="bg-white border-[#e4d8cb]"><Title className="text-[#6f655a]">Cash Credits</Title><Metric>{formatINR(data?.dashboard?.summary?.total_credits || 0)}</Metric></Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="bg-white border-[#e4d8cb]">
          <Title className="text-[#2a231d]">Cash & Burn Trend (6 months)</Title>
          <AreaChart
            data={history.length ? history : [{ month: selectedMonth, net_burn: 0, cash: 0 }]}
            index="month"
            categories={["net_burn", "cash"]}
            colors={["amber", "emerald"]}
            className="mt-4 h-72"
            valueFormatter={(n: number) => `₹${Intl.NumberFormat("en-IN").format(n)}`}
          />
        </Card>

        <Card className="bg-white border-[#e4d8cb]">
          <Title className="text-[#2a231d]">Burn By Category</Title>
          <BarChart
            data={Object.entries(summary?.breakdown_by_category || {}).map(([k, v]) => ({ category: k, amount: Number(v) }))}
            index="category"
            categories={["amount"]}
            colors={["amber"]}
            className="mt-4 h-60"
          />
        </Card>
      </div>

      <Card className="bg-white border-[#e4d8cb]">
        <Title className="text-[#2a231d]">AI Recommendations</Title>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
          {recommendations.slice(0, 6).map((rec: any, idx: number) => (
            <div key={idx} className="rounded-lg border border-[#e6dbcf] p-4 bg-[#fffdf9]">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-[#2a231d]">{rec.title || `Recommendation ${idx + 1}`}</p>
                <Badge color={rec.priority === "high" ? "red" : rec.priority === "medium" ? "amber" : "green"}>{rec.priority || "medium"}</Badge>
              </div>
              <p className="text-sm text-[#4f473d] mt-2">{rec.finding || rec.action}</p>
            </div>
          ))}
          {recommendations.length === 0 && <p className="text-sm text-[#7a6f62]">No recommendations available yet.</p>}
        </div>
      </Card>

      <Card className="bg-white border-[#e4d8cb]">
        <Title className="text-[#2a231d]">Product P&L</Title>
        <Table className="mt-4">
          <TableHead>
            <TableRow>
              <TableHeaderCell>Product</TableHeaderCell>
              <TableHeaderCell>Revenue</TableHeaderCell>
              <TableHeaderCell>Cost</TableHeaderCell>
              <TableHeaderCell>Gross Margin</TableHeaderCell>
              <TableHeaderCell>Margin %</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(products).map(([name, value]: any) => (
              <TableRow key={name}>
                <TableCell>{name}</TableCell>
                <TableCell>{formatINR(value.total_revenue)}</TableCell>
                <TableCell>{formatINR(value.total_cost)}</TableCell>
                <TableCell>{formatINR(value.gross_margin)}</TableCell>
                <TableCell>{value.gross_margin_pct?.toFixed?.(1) || 0}%</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {isLoading && <p className="text-sm text-[#7a6f62]">Loading dashboard data...</p>}
    </div>
  );
}
