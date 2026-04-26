"use client";

import { useEffect, useState } from "react";
import {
  AreaChart,
  Badge,
  BarChart,
  Card,
  DonutChart,
  Metric,
  ProgressBar,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  Title,
} from "@tremor/react";
import { TrendingDown, TrendingUp, AlertCircle, Target, Users, DollarSign } from "lucide-react";
import { useFinancialData } from "@/hooks/useFinancialData";
import api from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = API_BASE.replace(/\/$/, "").endsWith("/api/v1")
  ? API_BASE.replace(/\/$/, "")
  : `${API_BASE.replace(/\/$/, "")}/api/v1`;

const formatINR = (v: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v || 0);

const formatINRShort = (v: number) => {
  if (v >= 10_000_000) return `₹${(v / 10_000_000).toFixed(1)}Cr`;
  if (v >= 100_000) return `₹${(v / 100_000).toFixed(1)}L`;
  if (v >= 1_000) return `₹${(v / 1_000).toFixed(1)}K`;
  return `₹${v.toFixed(0)}`;
};

export default function CEODashboardPage() {
  const [companyId, setCompanyId] = useState<string>("");
  const [selectedMonth, setSelectedMonth] = useState<string>(new Date().toISOString().slice(0, 7));
  const [history, setHistory] = useState<any[]>([]);
  const [expenses, setExpenses] = useState<any>(null);

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
      if (payload.length > 0) {
        const availableMonths = new Set(payload.map((h: any) => h.month));
        const latestMonth = payload[payload.length - 1]?.month;
        if (latestMonth && !availableMonths.has(selectedMonth)) {
          setSelectedMonth(latestMonth);
        }
      }
    };
    loadHistory();
  }, [companyId, selectedMonth]);

  useEffect(() => {
    const loadExpenses = async () => {
      if (!companyId) return;
      const res = await fetch(`${API_V1}/burn/expenses/${companyId}?month=${selectedMonth}`);
      const payload = res.ok ? await res.json() : {};
      setExpenses(payload);
    };
    loadExpenses();
  }, [companyId, selectedMonth]);

  const summary = data?.dashboard?.summary || {};
  const products = data?.dashboard?.products || {};
  const headcount = data?.dashboard?.headcount || {};
  const recommendations = data?.recommendations?.recommendations || [];
  const alerts = data?.alerts || [];
  const burnMultiple = data?.dashboard?.multiple?.burn_multiple || 0;

  const breakdown = summary?.breakdown_by_category || {};
  const totalBurn = summary?.net_burn || 0;
  const cashBalance = summary?.total_credits || 0;
  const momChange = summary?.mom_change_pct || 0;

  const costByCategory = Object.entries(breakdown).map(([cat, amount]: any) => ({
    name: cat.replace(/_/g, " ").charAt(0).toUpperCase() + cat.slice(1).replace(/_/g, " "),
    value: Number(amount) || 0,
  }));

  const handleExportCsv = () => {
    if (!companyId) return;
    window.location.href = `${API_V1}/reports/export/ledger/csv?company_id=${companyId}`;
  };

  const handleExportPdf = () => {
    if (!companyId) return;
    window.location.href = `${API_V1}/reports/export/summary/pdf?company_id=${companyId}`;
  };

  const getStatusColor = (value: number, thresholds: { good: number; warning: number }) => {
    if (value <= thresholds.good) return "green";
    if (value <= thresholds.warning) return "amber";
    return "red";
  };

  return (
    <div className="min-h-screen bg-[#f6f3ee] text-[#1d1b19] p-6 md:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold text-[#1d1b19]">CEO Dashboard</h1>
          <p className="text-[#6f655a] mt-1">Financial health & strategic metrics for {selectedMonth}</p>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="bg-white border border-[#e1d3c2] rounded px-3 py-2 text-sm font-medium"
          />
          <button onClick={handleExportCsv} className="px-4 py-2 rounded bg-[#9a5d34] hover:bg-[#7f4c2a] text-white text-sm font-semibold transition">
            CSV
          </button>
          <button onClick={handleExportPdf} className="px-4 py-2 rounded bg-[#1f1a16] hover:bg-[#151210] text-white text-sm font-semibold transition">
            PDF
          </button>
        </div>
      </div>

      {/* Critical Alerts */}
      {alerts.length > 0 && (
        <div className="rounded-xl border border-red-300 bg-red-50 px-6 py-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-900">Runway Alert</p>
            <p className="text-sm text-red-700 mt-1">⚠️ Only {alerts[0]?.runway_months || "unknown"} months of cash remaining at current burn rate. Immediate action required.</p>
          </div>
        </div>
      )}

      {/* Top KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card className="bg-gradient-to-br from-red-50 to-red-100/50 border-red-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[#6f655a] text-xs font-semibold uppercase">Net Burn</p>
              <Metric className="mt-1">{formatINRShort(totalBurn)}</Metric>
              <p className={`text-xs mt-2 font-medium ${momChange < 0 ? "text-green-600" : "text-red-600"} flex items-center gap-1`}>
                {momChange < 0 ? <TrendingDown className="w-3 h-3" /> : <TrendingUp className="w-3 h-3" />}
                {Math.abs(momChange).toFixed(1)}% vs last month
              </p>
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-amber-50 to-amber-100/50 border-amber-200">
          <div>
            <p className="text-[#6f655a] text-xs font-semibold uppercase">Burn Multiple</p>
            <Metric className="mt-1">{burnMultiple.toFixed(2)}x</Metric>
            <p className="text-xs text-[#6f655a] mt-2">Target: 1.5x (Industry standard)</p>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100/50 border-emerald-200">
          <div>
            <p className="text-[#6f655a] text-xs font-semibold uppercase">Cash Balance</p>
            <Metric className="mt-1">{formatINRShort(cashBalance)}</Metric>
            <p className="text-xs text-[#6f655a] mt-2">Runway: {cashBalance > 0 ? ((cashBalance / (totalBurn || 1)) * 30).toFixed(0) : "0"} days</p>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100/50 border-blue-200">
          <div>
            <p className="text-[#6f655a] text-xs font-semibold uppercase">Headcount</p>
            <Metric className="mt-1">{headcount.total_headcount || 0}</Metric>
            <p className="text-xs text-[#6f655a] mt-2">Cost per head: {formatINRShort((headcount.per_employee_cost || 0) / 12)}/mo</p>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100/50 border-purple-200">
          <div>
            <p className="text-[#6f655a] text-xs font-semibold uppercase">GM Avg</p>
            <Metric className="mt-1">
              {(Object.values(products).reduce((sum: number, p: any) => sum + (p.gross_margin_pct || 0), 0) / (Object.keys(products).length || 1)).toFixed(1)}%
            </Metric>
            <p className="text-xs text-[#6f655a] mt-2">Across {Object.keys(products).length} products</p>
          </div>
        </Card>
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 bg-white border-[#e4d8cb]">
          <Title className="text-[#2a231d]">6-Month Burn & Cash Trajectory</Title>
          <AreaChart
            data={history.slice(-6).map((h: any) => ({
              month: h.month,
              "Net Burn": Number(h.net_burn || 0),
              Cash: Number(h.cash || 0),
            }))}
            index="month"
            categories={["Net Burn", "Cash"]}
            colors={["red", "emerald"]}
            className="mt-4 h-64"
            valueFormatter={(n: number) => formatINRShort(n)}
          />
        </Card>

        <Card className="bg-white border-[#e4d8cb]">
          <Title className="text-[#2a231d]">Cost Breakdown</Title>
          <DonutChart
            data={costByCategory.slice(0, 6)}
            category="value"
            index="name"
            colors={["red", "amber", "blue", "green", "purple", "indigo"]}
            className="mt-4 h-64"
            valueFormatter={(n: number) => formatINRShort(n)}
          />
        </Card>
      </div>

      {/* Financial Health Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cost Drivers */}
        <Card className="bg-white border-[#e4d8cb]">
          <Title className="text-[#2a231d]">Top Cost Drivers</Title>
          <div className="mt-6 space-y-4">
            {costByCategory.slice(0, 5).map((item: any, idx: number) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-[#2a231d]">{item.name}</span>
                  <span className="text-sm font-semibold text-[#6f655a]">{((item.value / totalBurn) * 100).toFixed(1)}%</span>
                </div>
                <ProgressBar value={((item.value / totalBurn) * 100)} color="amber" className="w-full" />
              </div>
            ))}
          </div>
        </Card>

        {/* Financial Metrics */}
        <Card className="bg-white border-[#e4d8cb]">
          <Title className="text-[#2a231d]">Key Metrics & Ratios</Title>
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between py-2 border-b border-[#e6dbcf]">
              <span className="text-sm text-[#6f655a]">Revenue per Employee</span>
              <span className="font-semibold text-[#2a231d]">{formatINRShort((summary.total_credits || 0) / Math.max(headcount.total_headcount || 1, 1))}/mo</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-[#e6dbcf]">
              <span className="text-sm text-[#6f655a]">Avg Cost per Employee</span>
              <span className="font-semibold text-[#2a231d]">{formatINRShort((headcount.per_employee_cost || 0) / 12)}/mo</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-[#e6dbcf]">
              <span className="text-sm text-[#6f655a]">Headcount Ratio</span>
              <span className="font-semibold text-[#2a231d]">{(((summary.total_credits || 0) / (headcount.per_employee_cost || 1)) * 100).toFixed(0)}%</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-[#6f655a]">Cash Position</span>
              <span className="font-semibold text-[#2a231d]">{formatINRShort(cashBalance)}</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Product Performance */}
      <Card className="bg-white border-[#e4d8cb]">
        <Title className="text-[#2a231d]">Product Performance & Profitability</Title>
        <Table className="mt-6">
          <TableHead>
            <TableRow>
              <TableHeaderCell>Product</TableHeaderCell>
              <TableHeaderCell>Revenue</TableHeaderCell>
              <TableHeaderCell>Cost</TableHeaderCell>
              <TableHeaderCell>Gross Margin</TableHeaderCell>
              <TableHeaderCell>Margin %</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(products)
              .sort((a: any, b: any) => (b[1]?.gross_margin || 0) - (a[1]?.gross_margin || 0))
              .map(([name, value]: any) => {
                const marginPct = value.gross_margin_pct || 0;
                const status = marginPct > 50 ? "Healthy" : marginPct > 30 ? "Monitor" : "Critical";
                return (
                  <TableRow key={name}>
                    <TableCell className="font-semibold capitalize">{name.replace(/_/g, " ")}</TableCell>
                    <TableCell>{formatINRShort(value.total_revenue || 0)}</TableCell>
                    <TableCell>{formatINRShort(value.total_cost || 0)}</TableCell>
                    <TableCell className="font-semibold">{formatINRShort(value.gross_margin || 0)}</TableCell>
                    <TableCell>
                      <Badge color={marginPct > 50 ? "green" : marginPct > 30 ? "amber" : "red"}>{marginPct.toFixed(1)}%</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge color={status === "Healthy" ? "green" : status === "Monitor" ? "amber" : "red"}>{status}</Badge>
                    </TableCell>
                  </TableRow>
                );
              })}
          </TableBody>
        </Table>
      </Card>

      {/* AI-Powered Recommendations */}
      <Card className="bg-white border-[#e4d8cb]">
        <div className="flex items-center gap-2 mb-4">
          <Target className="w-5 h-5 text-[#2a231d]" />
          <Title className="text-[#2a231d]">AI-Powered Recommendations</Title>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          {recommendations.slice(0, 6).map((rec: any, idx: number) => (
            <div key={idx} className={`rounded-lg border p-4 ${rec.priority === "high" ? "bg-red-50 border-red-200" : rec.priority === "medium" ? "bg-amber-50 border-amber-200" : "bg-green-50 border-green-200"}`}>
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <p className={`font-semibold ${rec.priority === "high" ? "text-red-900" : rec.priority === "medium" ? "text-amber-900" : "text-green-900"}`}>
                    {rec.title || `Action ${idx + 1}`}
                  </p>
                  <p className={`text-sm mt-1 ${rec.priority === "high" ? "text-red-700" : rec.priority === "medium" ? "text-amber-700" : "text-green-700"}`}>
                    {rec.finding || rec.action}
                  </p>
                </div>
              </div>
            </div>
          ))}
          {recommendations.length === 0 && (
            <div className="col-span-2 text-center py-6 text-[#7a6f62]">No recommendations available yet. Add financial data to get insights.</div>
          )}
        </div>
      </Card>

      {isLoading && <p className="text-center text-sm text-[#7a6f62]">Loading your financial dashboard...</p>}
    </div>
  );
}
