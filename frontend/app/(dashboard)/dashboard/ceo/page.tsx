"use client";

import { useMemo } from "react";
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

const companyId = "00000000-0000-0000-0000-000000000001";

const formatINR = (v: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v || 0);

export default function CEODashboardPage() {
  const month = useMemo(() => new Date().toISOString().slice(0, 7), []);
  const { data, isLoading } = useFinancialData(companyId, month);

  const summary = data?.dashboard?.summary || {};
  const products = data?.dashboard?.products || {};
  const recommendations = data?.recommendations?.recommendations || [];
  const alerts = data?.alerts || [];
  
  // Use historical data if available, fallback to single point
  const history = data?.dashboard?.history || (data?.dashboard?.summary ? [data.dashboard.summary] : []);

  const handleExport = () => {
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/reports/export/ledger/csv?company_id=${companyId}`;
  };

  return (
    <div className="min-h-screen bg-[#0b1020] text-slate-100 p-8 space-y-6">
      <div className="flex items-center justify-between">
        <Title className="text-slate-100">Seedling Labs - Finance Overview ({month})</Title>
        <div className="flex gap-3">
          <button 
            onClick={handleExport}
            className="flex items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-700"
          >
            Export CSV
          </button>
        </div>
      </div>

      {alerts.length > 0 && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3">
          <p className="text-sm font-semibold text-rose-200">Runway alert active: {alerts[0]?.runway_months} months remaining.</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-slate-900 border-slate-800">
          <Title className="text-slate-400">Runway</Title>
          <div className="flex items-baseline gap-2">
            <Metric>{summary?.net_burn ? `${(summary.net_burn / 100000).toFixed(1)} mo` : "-"}</Metric>
            <Badge color="emerald" className="bg-emerald-500/20 text-emerald-400 border-emerald-500/20">+1.2</Badge>
          </div>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <Title className="text-slate-400">Net Burn</Title>
          <div className="flex items-baseline gap-2">
            <Metric>{formatINR(summary?.net_burn || 0)}</Metric>
            <Badge color="rose" className="bg-rose-500/20 text-rose-400 border-rose-500/20">-4.2%</Badge>
          </div>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <Title className="text-slate-400">Burn Multiple</Title>
          <div className="flex items-baseline gap-2">
            <Metric>{data?.dashboard?.multiple?.burn_multiple?.toFixed?.(2) || "0.00"}x</Metric>
            <Badge color="emerald" className="bg-emerald-500/20 text-emerald-400 border-emerald-500/20">-0.2</Badge>
          </div>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <Title className="text-slate-400">Cash Balance</Title>
          <div className="flex items-baseline gap-2">
            <Metric>{formatINR(data?.dashboard?.summary?.total_credits || 0)}</Metric>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="bg-slate-900 border-slate-800">
          <Title className="text-slate-400">Cash & Burn Trend</Title>
          <AreaChart
            data={history}
            index="month"
            categories={["net_burn", "total_credits"]}
            colors={["cyan", "blue"]}
            className="mt-4 h-72"
            valueFormatter={(number: number) => `₹${Intl.NumberFormat("en").format(number).toString()}`}
          />
        </Card>
        <Card>
          <Title>Burn By Category</Title>
          <BarChart
            data={Object.entries(summary?.breakdown_by_category || {}).map(([k, v]) => ({ category: k, amount: Number(v) }))}
            index="category"
            categories={["amount"]}
            colors={["blue"]}
            className="mt-4 h-60"
          />
        </Card>
      </div>

      <Card>
        <Title>AI Recommendations</Title>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
          {recommendations.slice(0, 6).map((rec: any, idx: number) => (
            <div key={idx} className="rounded-lg border border-white/10 p-4 bg-white/5">
              <div className="flex items-center justify-between">
                <p className="font-semibold">{rec.title || `Recommendation ${idx + 1}`}</p>
                <Badge color={rec.priority === "high" ? "red" : rec.priority === "medium" ? "amber" : "green"}>{rec.priority || "medium"}</Badge>
              </div>
              <p className="text-sm text-slate-300 mt-2">{rec.finding || rec.action}</p>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <Title>Product P&L</Title>
        <Table className="mt-4">
          <TableHead>
            <TableRow>
              <TableHeaderCell>Product</TableHeaderCell>
              <TableHeaderCell>Revenue</TableHeaderCell>
              <TableHeaderCell>Cost</TableHeaderCell>
              <TableHeaderCell>Gross Margin</TableHeaderCell>
              <TableHeaderCell>Runway Impact</TableHeaderCell>
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

      {isLoading && <p className="text-sm text-slate-400">Loading dashboard data...</p>}
    </div>
  );
}
