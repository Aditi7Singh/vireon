"use client";

import { useEffect, useMemo, useState } from "react";
import { BarChart, Card, Table, TableBody, TableCell, TableHead, TableHeaderCell, TableRow, Title } from "@tremor/react";
import { useFinancialData } from "@/hooks/useFinancialData";
import api, { FinancialConceptResponse, FinancialRecommendationsResponse } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = API_BASE.replace(/\/$/, "").endsWith("/api/v1") ? API_BASE.replace(/\/$/, "") : `${API_BASE.replace(/\/$/, "")}/api/v1`;
const formatINR = (v: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v || 0);

export default function FinanceDashboardPage() {
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
  const [companyId, setCompanyId] = useState<string>("");
  const [pendingReview, setPendingReview] = useState<Record<string, any[]>>({});
  const [reconciliation, setReconciliation] = useState<{ netBurn: number; expenseTotal: number; variance: number } | null>(null);
  const [trendSeries, setTrendSeries] = useState<Array<{ month: string; revenue: number; net_burn: number; cash: number }>>([]);
  const [financialRecommendations, setFinancialRecommendations] = useState<FinancialRecommendationsResponse | null>(null);
  const [currentRatioConcept, setCurrentRatioConcept] = useState<FinancialConceptResponse | null>(null);
  const { data, isLoading } = useFinancialData(companyId, month);

  useEffect(() => {
    const load = async () => {
      const health = await api.getStartupHealth();
      const cid = health.default_company_id || "";
      setCompanyId(cid);
      if (!cid) return;
      const historyRes = await fetch(`${API_V1}/metrics/history/${cid}?months=6`);
      if (historyRes.ok) {
        const history = await historyRes.json();
        const latestMonth = history?.[history.length - 1]?.month;
        if (latestMonth) setMonth(latestMonth);
      }
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
      const historyRes = await fetch(`${API_V1}/metrics/history/${companyId}?months=6`);

      const pending = pendingRes.ok ? await pendingRes.json() : { pending_review: {} };
      const burn = burnRes.ok ? await burnRes.json() : { net_burn: 0 };
      const expenses = expensesRes.ok ? await expensesRes.json() : { tech_costs: {}, non_tech_costs: {} };
      const history = historyRes.ok ? await historyRes.json() : [];

      setPendingReview(pending.pending_review || {});

      const techTotal = Number(expenses.tech_costs?.aws_total || 0) + Number(expenses.tech_costs?.licenses_total || 0) + Number(expenses.tech_costs?.saas_total || 0);
      const nonTechTotal = Number(expenses.non_tech_costs?.marketing || 0) + Number(expenses.non_tech_costs?.office_bengaluru || 0) + Number(expenses.non_tech_costs?.office_gangavathi || 0) + Number(expenses.non_tech_costs?.misc || 0);
      const expenseTotal = techTotal + nonTechTotal;
      const netBurn = Number(burn.net_burn || 0);
      setReconciliation({ netBurn, expenseTotal, variance: netBurn - expenseTotal });
      setTrendSeries(history.map((h: any) => ({
        month: h.month,
        revenue: Number(h.revenue || 0),
        net_burn: Number(h.net_burn || 0),
        cash: Number(h.cash || 0),
      })));
    };
    loadFinance();
  }, [companyId, month]);

  useEffect(() => {
    const loadFinancialInsights = async () => {
      if (!companyId) return;

      try {
        const [scorecard, revenue, cashBalance, runway] = await Promise.all([
          api.getScorecard(),
          api.getRevenue(),
          api.getCashBalance(),
          api.getRunway(),
        ]);

        const recommendations = await api.getFinancialRecommendations({
          company_id: companyId,
          company_stage: "growth",
          financial_metrics: {
            revenue: scorecard.monthly_revenue || revenue.mrr,
            net_income: scorecard.monthly_revenue - scorecard.monthly_net_burn,
            gross_margin: scorecard.monthly_revenue > 0 ? Math.max(0, 1 - (scorecard.monthly_gross_burn / Math.max(scorecard.monthly_revenue, 1))) * 100 : 0,
            current_ratio: cashBalance.net_cash > 0 ? 1.5 : 0.9,
            debt_to_equity: 0.8,
            cash_conversion_cycle: 45,
            monthly_burn: scorecard.monthly_net_burn,
            cash_balance: cashBalance.cash,
            runway_months: runway.runway_months,
          },
        });

        const concept = await api.getFinancialConcept("current_ratio");
        setFinancialRecommendations(recommendations);
        setCurrentRatioConcept(concept);
      } catch {
        setFinancialRecommendations(null);
        setCurrentRatioConcept(null);
      }
    };

    void loadFinancialInsights();
  }, [companyId]);

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

  async function exportLedgerCsv() {
    if (!companyId) return;
    const res = await fetch(`${API_V1}/reports/export/ledger/csv?company_id=${companyId}`);
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `finance-ledger-${companyId}-${month}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  async function exportSummaryPdf() {
    if (!companyId) return;
    const res = await fetch(`${API_V1}/reports/export/summary/pdf?company_id=${companyId}`);
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `finance-summary-${companyId}-${month}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="min-h-screen bg-[#f6f3ee] text-[#1d1b19] p-6 md:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold text-[#1d1b19]">Finance Control</h1>
          <p className="text-[#6f655a] mt-1">Detailed ledger analysis & reconciliation for {month}</p>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="month"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="bg-white border border-[#e1d3c2] rounded-lg px-3 py-2 font-medium text-sm"
          />
          <button onClick={exportLedgerCsv} className="px-4 py-2 rounded-lg bg-[#9a5d34] hover:bg-[#7f4c2a] text-white text-sm font-semibold transition">Export CSV</button>
          <button onClick={exportSummaryPdf} className="px-4 py-2 rounded-lg bg-[#1f1a16] hover:bg-[#151210] text-white text-sm font-semibold transition">Export PDF</button>
        </div>
      </div>

      {/* Summary Cards */}
      {reconciliation && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100/50 border-blue-200">
            <div>
              <p className="text-[#6f655a] text-xs font-semibold uppercase">Net Burn</p>
              <p className="mt-2 text-3xl font-bold text-[#1d1b19]">{formatINR(reconciliation.netBurn)}</p>
              <p className="text-xs text-[#6f655a] mt-1">Monthly cash burn rate</p>
            </div>
          </Card>
          <Card className="bg-gradient-to-br from-amber-50 to-amber-100/50 border-amber-200">
            <div>
              <p className="text-[#6f655a] text-xs font-semibold uppercase">Total Expenses</p>
              <p className="mt-2 text-3xl font-bold text-[#1d1b19]">{formatINR(reconciliation.expenseTotal)}</p>
              <p className="text-xs text-[#6f655a] mt-1">Tech + Non-tech costs</p>
            </div>
          </Card>
          <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100/50 border-emerald-200">
            <div>
              <p className="text-[#6f655a] text-xs font-semibold uppercase">Variance</p>
              <p className={`mt-2 text-3xl font-bold ${Math.abs(reconciliation.variance) < 50000 ? "text-emerald-600" : "text-red-600"}`}>
                {Math.abs(reconciliation.variance) < 50000 ? "✓ Reconciled" : `${formatINR(reconciliation.variance)}`}
              </p>
              <p className="text-xs text-[#6f655a] mt-1">Burn vs expenses</p>
            </div>
          </Card>
        </div>
      )}

      {financialRecommendations && currentRatioConcept && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card className="bg-white border-[#e4d8cb]">
            <Title className="text-[#2a231d]">Financial Recommendations</Title>
            <div className="mt-4 space-y-3">
              {(financialRecommendations.recommendations || []).slice(0, 3).map((item, idx) => (
                <div key={idx} className="rounded-lg border border-[#eadfcd] bg-[#fffdf8] p-3">
                  <p className="font-semibold text-[#2a231d]">{String(item.title || item.area || `Recommendation ${idx + 1}`)}</p>
                  <p className="text-sm text-[#6f655a] mt-1">{String(item.rationale || item.finding || item.action || "Action required")}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card className="bg-white border-[#e4d8cb]">
            <Title className="text-[#2a231d]">Current Ratio Concept</Title>
            <div className="mt-4 space-y-2 text-sm text-[#4f453a]">
              <p><strong>Definition:</strong> {currentRatioConcept.definition}</p>
              <p><strong>Interpretation:</strong> {currentRatioConcept.interpretation}</p>
              <p><strong>Good range:</strong> {currentRatioConcept.good_range}</p>
            </div>
          </Card>
        </div>
      )}

      {/* Trends Chart */}
      <Card className="bg-white border-[#e4d8cb]">
        <Title className="text-[#2a231d]">6-Month Financial Trends</Title>
        <BarChart
          className="mt-6 h-80"
          data={trendSeries.length ? trendSeries : [{ month, revenue: 0, net_burn: 0, cash: 0 }]}
          index="month"
          categories={["revenue", "net_burn", "cash"]}
          colors={["emerald", "red", "blue"]}
          valueFormatter={(v) => `${(v / 100000).toFixed(1)}L`}
        />
      </Card>

      {/* Expense Breakdown Table */}
      <Card className="bg-white border-[#e4d8cb]">
        <Title className="text-[#2a231d]">Expense Breakdown by Category</Title>
        <Table className="mt-6">
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
            {rows.length > 0 ? rows.map((r, idx) => (
              <TableRow key={idx}>
                <TableCell className="capitalize font-semibold">{r.category.replace(/_/g, " ")}</TableCell>
                <TableCell className="capitalize">{r.product}</TableCell>
                <TableCell className="font-semibold">{formatINR(r.amount)}</TableCell>
                <TableCell className="capitalize">{r.type}</TableCell>
                <TableCell className="capitalize">{r.source}</TableCell>
                <TableCell>{r.date}</TableCell>
              </TableRow>
            )) : (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-6 text-[#7a6f62]">No expense data available for this period</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Pending Review Items */}
      {Object.keys(pendingReview).length > 0 && (
        <Card className="bg-white border-[#e4d8cb]">
          <Title className="text-[#2a231d]">Items Pending Review</Title>
          <div className="mt-6 space-y-3">
            {Object.entries(pendingReview).map(([category, items]: any) => (
              <div key={category} className="border-l-4 border-amber-400 pl-4 py-2">
                <p className="font-semibold text-[#2a231d] capitalize">{category.replace(/_/g, " ")}</p>
                <p className="text-sm text-[#6f655a] mt-1">{items.length} items requiring approval</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <p className="text-[#7a6f62]">Loading financial data...</p>
        </div>
      )}
    </div>
  );
}
