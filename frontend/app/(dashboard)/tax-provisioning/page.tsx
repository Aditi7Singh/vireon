"use client";

import { useEffect, useState } from "react";
import { Card, Title } from "@tremor/react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { Calculator, TrendingDown, Play, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = `${API_BASE.replace(/\/$/, "")}/api/v1`;

type TaxResult = {
  jurisdiction: string;
  state: string | null;
  period: string;
  taxable_income: number;
  total_revenue: number;
  total_expenses: number;
  corporate_tax: {
    total_tax: number;
    effective_rate: number;
    remaining_due: number;
    federal_tax?: number;
    state_tax?: number;
  };
  payroll_tax: { total_employer_tax: number; effective_rate_pct: number };
  rd_credit: { estimated_credit: number; qualifying_expenses: number; credit_rate: string };
  net_tax_after_credits: number;
  quarterly_schedule: {
    schedule: Array<{ quarter: string; due_date: string; amount: number; status: string }>;
    annual_estimate: number;
    remaining_balance: number;
    catch_up_per_quarter: number;
  };
  deduction_opportunities: Array<{
    type: string;
    amount: number;
    potential_saving: number;
    description: string;
    action: string;
  }>;
  total_deduction_savings: number;
  summary: string;
};

const JURISDICTIONS = ["US", "UK", "Dubai", "India", "Singapore", "EU"];

export default function TaxProvisioningPage() {
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TaxResult | null>(null);
  const [jurisdiction, setJurisdiction] = useState("US");
  const [state, setState] = useState("CA");
  const [showDeductions, setShowDeductions] = useState(false);
  const [showSchedule, setShowSchedule] = useState(false);
  const [companyId, setCompanyId] = useState<string>("");

  useEffect(() => {
    const bootstrapCompany = async () => {
      try {
        const token = localStorage.getItem("access_token") || localStorage.getItem("auth_token") || "";
        const healthRes = await fetch(`${API_V1}/system/startup-health`, {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        });
        if (healthRes.ok) {
          const health = await healthRes.json();
          if (health?.default_company_id) {
            setCompanyId(String(health.default_company_id));
          }
        }
      } catch {
        // Keep silent; runtime fallback is handled in runProvisioning.
      }
    };
    void bootstrapCompany();
  }, []);

  const runProvisioning = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("access_token") || localStorage.getItem("auth_token") || "";
      const cid = companyId || localStorage.getItem("company_id") || "";
      const quarter = Math.ceil((new Date().getMonth() + 1) / 3);
      const params = new URLSearchParams({
        company_id: cid,
        jurisdiction,
        current_quarter: String(quarter),
      });
      if (jurisdiction === "US" && state) params.set("state", state);

      const res = await fetch(`${API_V1}/phase3/tax/provision?${params}`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch {
      const defaultRates: Record<string, number> = {
        US: 0.30,
        UK: 0.25,
        Dubai: 0.09,
        India: 0.25,
        Singapore: 0.17,
        EU: 0.22,
      };
      const effectiveRate = (defaultRates[jurisdiction] || 0.25) * 100;
      const taxableIncome = 820000;
      const corporateTaxTotal = Math.round(taxableIncome * (effectiveRate / 100));
      // Demo fallback
      setResult({
        jurisdiction,
        state: jurisdiction === "US" ? state : null,
        period: `Q${Math.ceil((new Date().getMonth() + 1) / 3)} ${new Date().getFullYear()}`,
        taxable_income: taxableIncome,
        total_revenue: 1500000,
        total_expenses: 680000,
        corporate_tax: {
          total_tax: corporateTaxTotal,
          effective_rate: Number(effectiveRate.toFixed(2)),
          remaining_due: Math.round(corporateTaxTotal * 0.8),
          federal_tax: jurisdiction === "US" ? 172200 : undefined,
          state_tax: jurisdiction === "US" ? 72660 : undefined,
        },
        payroll_tax: { total_employer_tax: 109500, effective_rate_pct: 10.95 },
        rd_credit: { estimated_credit: 24000, qualifying_expenses: 120000, credit_rate: "20%" },
        net_tax_after_credits: Math.max(corporateTaxTotal - 24000, 0),
        quarterly_schedule: {
          schedule: [
            { quarter: "Q1", due_date: "Apr 15", amount: 88590, status: "past" },
            { quarter: "Q2", due_date: "Jun 15", amount: 88590, status: "due_now" },
            { quarter: "Q3", due_date: "Sep 15", amount: 88590, status: "upcoming" },
            { quarter: "Q4", due_date: "Jan 15", amount: 88590, status: "upcoming" },
          ],
          annual_estimate: Math.round(corporateTaxTotal * 1.45),
          remaining_balance: Math.round(corporateTaxTotal * 1.1),
          catch_up_per_quarter: 88590,
        },
        deduction_opportunities: [
          {
            type: "R&D Tax Credit",
            amount: 120000,
            potential_saving: 24000,
            description: "$120,000 in R&D expenses may qualify for Section 41 credit ($24,000 benefit).",
            action: "File Form 6765 with CPA",
          },
          {
            type: "Business Meals (50%)",
            amount: 18500,
            potential_saving: 1939,
            description: "$18,500 in meals/entertainment — 50% deductible = $9,250 deduction.",
            action: "Ensure receipts and business purpose are documented",
          },
          {
            type: "Remote Work Expenses",
            amount: 12300,
            potential_saving: 2583,
            description: "$12,300 in remote-work-related expenses may be fully deductible.",
            action: "Allocate to business use and document percentage",
          },
        ],
        total_deduction_savings: 28522,
        summary: `${jurisdiction} tax estimate ready. Effective corporate tax rate: ${effectiveRate.toFixed(1)}%. Fallback mode is showing demo assumptions until live endpoint responds.`,
      });
    } finally {
      setLoading(false);
    }
  };

  const statusColor = (s: string) =>
    s === "due_now" ? "bg-red-100 text-red-700" :
    s === "past" ? "bg-gray-100 text-gray-500" :
    "bg-blue-100 text-blue-700";

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#fdf9f4]">
      <TopBar title="Tax Provisioning" />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* Header + Controls */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-[#3d2c1e]">Predictive Tax Provisioning</h1>
            <p className="text-sm text-[#8c6a4a] mt-1">
              Multi-jurisdiction corporate tax, payroll tax, R&D credits, and deduction optimizer
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={jurisdiction}
              onChange={(e) => setJurisdiction(e.target.value)}
              className="text-sm border border-[#e3d6c7] rounded-lg px-3 py-2 bg-white text-[#3d2c1e] focus:outline-none"
            >
              {JURISDICTIONS.map((j) => (
                <option key={j} value={j}>{j}</option>
              ))}
            </select>
            {jurisdiction === "US" && (
              <select
                value={state}
                onChange={(e) => setState(e.target.value)}
                className="text-sm border border-[#e3d6c7] rounded-lg px-3 py-2 bg-white text-[#3d2c1e] focus:outline-none"
              >
                {["CA", "NY", "TX", "DE", "WA", "FL"].map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            )}
            <button
              onClick={runProvisioning}
              disabled={loading}
              className={cn(
                "flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all shadow-sm",
                loading
                  ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                  : "bg-[#c8873a] text-white hover:bg-[#a86d2a] active:scale-95"
              )}
            >
              <Calculator className="w-4 h-4" />
              {loading ? "Computing…" : "Compute Tax"}
            </button>
          </div>
        </div>

        {result && (
          <>
            {/* Summary strip */}
            <div className="bg-[#fff8f0] border border-[#e3d6c7] rounded-2xl p-4">
              <p className="text-sm text-[#6b4c2c]">{result.summary}</p>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Taxable Income", value: `$${result.taxable_income.toLocaleString()}`, color: "text-[#3d2c1e]" },
                { label: "Total Tax", value: `$${result.corporate_tax.total_tax.toLocaleString()}`, color: "text-red-600" },
                { label: "R&D Credit", value: `$${result.rd_credit.estimated_credit.toLocaleString()}`, color: "text-green-600" },
                { label: "Net Tax Due", value: `$${result.net_tax_after_credits.toLocaleString()}`, color: "text-amber-600" },
              ].map((kpi) => (
                <Card key={kpi.label} className="bg-white border border-[#e3d6c7] rounded-2xl p-4">
                  <p className="text-xs text-[#8c6a4a] font-medium">{kpi.label}</p>
                  <p className={cn("text-2xl font-bold mt-1", kpi.color)}>{kpi.value}</p>
                </Card>
              ))}
            </div>

            {/* Tax breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="bg-white border border-[#e3d6c7] rounded-2xl p-5">
                <Title className="text-sm font-semibold text-[#3d2c1e] mb-4">Corporate Tax</Title>
                <dl className="space-y-2 text-sm">
                  {result.corporate_tax.federal_tax !== undefined && (
                    <div className="flex justify-between">
                      <dt className="text-[#8c6a4a]">Federal Tax (21%)</dt>
                      <dd className="font-semibold text-[#3d2c1e]">${result.corporate_tax.federal_tax.toLocaleString()}</dd>
                    </div>
                  )}
                  {result.corporate_tax.state_tax !== undefined && (
                    <div className="flex justify-between">
                      <dt className="text-[#8c6a4a]">State Tax ({result.state})</dt>
                      <dd className="font-semibold text-[#3d2c1e]">${result.corporate_tax.state_tax.toLocaleString()}</dd>
                    </div>
                  )}
                  <div className="flex justify-between border-t pt-2">
                    <dt className="text-[#8c6a4a] font-medium">Effective Rate</dt>
                    <dd className="font-bold text-[#3d2c1e]">{result.corporate_tax.effective_rate.toFixed(1)}%</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-[#8c6a4a] font-medium">Still Owed</dt>
                    <dd className="font-bold text-red-600">${result.corporate_tax.remaining_due.toLocaleString()}</dd>
                  </div>
                </dl>
              </Card>

              <Card className="bg-white border border-[#e3d6c7] rounded-2xl p-5">
                <Title className="text-sm font-semibold text-[#3d2c1e] mb-4">R&D Credit Analysis</Title>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-[#8c6a4a]">Qualifying Expenses</dt>
                    <dd className="font-semibold text-[#3d2c1e]">${result.rd_credit.qualifying_expenses.toLocaleString()}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-[#8c6a4a]">Credit Rate</dt>
                    <dd className="font-semibold text-[#3d2c1e]">{result.rd_credit.credit_rate}</dd>
                  </div>
                  <div className="flex justify-between border-t pt-2">
                    <dt className="font-medium text-green-700">Estimated Credit</dt>
                    <dd className="font-bold text-green-600">${result.rd_credit.estimated_credit.toLocaleString()}</dd>
                  </div>
                </dl>
              </Card>
            </div>

            {/* Quarterly Schedule */}
            <Card className="bg-white border border-[#e3d6c7] rounded-2xl overflow-hidden">
              <button
                className="w-full p-5 text-left flex items-center justify-between"
                onClick={() => setShowSchedule(!showSchedule)}
              >
                <Title className="text-sm font-semibold text-[#3d2c1e]">Quarterly Payment Schedule</Title>
                {showSchedule ? <ChevronUp className="w-4 h-4 text-[#8c6a4a]" /> : <ChevronDown className="w-4 h-4 text-[#8c6a4a]" />}
              </button>
              {showSchedule && (
                <div className="px-5 pb-5">
                  <div className="grid grid-cols-4 gap-2 mb-4">
                    {result.quarterly_schedule.schedule.map((q) => (
                      <div key={q.quarter} className={cn("rounded-xl p-3 text-center", statusColor(q.status))}>
                        <p className="text-xs font-medium">{q.quarter}</p>
                        <p className="text-sm font-bold mt-1">${q.amount.toLocaleString()}</p>
                        <p className="text-xs mt-1">{q.due_date}</p>
                      </div>
                    ))}
                  </div>
                  <div className="text-sm text-[#8c6a4a] space-y-1 border-t pt-3">
                    <div className="flex justify-between">
                      <span>Annual Estimate</span>
                      <span className="font-semibold text-[#3d2c1e]">${result.quarterly_schedule.annual_estimate.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Remaining Balance</span>
                      <span className="font-semibold text-red-600">${result.quarterly_schedule.remaining_balance.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              )}
            </Card>

            {/* Deduction Opportunities */}
            {result.deduction_opportunities.length > 0 && (
              <Card className="bg-white border border-[#e3d6c7] rounded-2xl overflow-hidden">
                <button
                  className="w-full p-5 text-left flex items-center justify-between"
                  onClick={() => setShowDeductions(!showDeductions)}
                >
                  <div className="flex items-center gap-3">
                    <TrendingDown className="w-4 h-4 text-green-600" />
                    <Title className="text-sm font-semibold text-[#3d2c1e]">
                      Deduction Opportunities
                    </Title>
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
                      Save ${result.total_deduction_savings.toLocaleString()}
                    </span>
                  </div>
                  {showDeductions ? <ChevronUp className="w-4 h-4 text-[#8c6a4a]" /> : <ChevronDown className="w-4 h-4 text-[#8c6a4a]" />}
                </button>
                {showDeductions && (
                  <div className="px-5 pb-5 space-y-3">
                    {result.deduction_opportunities.map((d, idx) => (
                      <div key={idx} className="bg-[#fdf5ea] rounded-xl p-4 text-sm">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-semibold text-[#3d2c1e]">{d.type}</span>
                          <span className="text-green-600 font-bold">Save ${d.potential_saving.toLocaleString()}</span>
                        </div>
                        <p className="text-[#8c6a4a] text-xs">{d.description}</p>
                        <p className="text-[#c8873a] text-xs mt-1 font-medium">→ {d.action}</p>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )}
          </>
        )}

        {!result && !loading && (
          <Card className="bg-white border border-[#e3d6c7] rounded-2xl p-12 flex flex-col items-center justify-center text-center">
            <Calculator className="w-12 h-12 text-[#c8873a] mb-4 opacity-60" />
            <p className="text-lg font-semibold text-[#3d2c1e]">Compute Tax Provision</p>
            <p className="text-sm text-[#8c6a4a] mt-2 max-w-sm">
              Get quarterly estimates, R&D credits, and deduction opportunities for {jurisdiction}.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
