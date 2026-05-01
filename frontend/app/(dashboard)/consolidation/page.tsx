"use client";

import { useEffect, useState } from "react";
import { Card, Title } from "@tremor/react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { Building2, RefreshCw, CheckCircle, XCircle, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = `${API_BASE.replace(/\/$/, "")}/api/v1`;

type Entity = {
  id: string;
  name: string;
  currency: string;
  revenue: number;
  expenses: number;
  cash: number;
};

type ConsolidationResult = {
  entities: Entity[];
  consolidated: {
    total_revenue: number;
    total_expenses: number;
    total_cash: number;
    net_income: number;
    entity_count: number;
  };
  intercompany_eliminations: number;
  fx_adjustments: Record<string, number>;
};

const CURRENCIES = ["USD", "GBP", "EUR", "AED", "INR", "SGD"];

const DEMO_ENTITIES: Entity[] = [
  { id: "1", name: "Vireon US (HQ)", currency: "USD", revenue: 980000, expenses: 620000, cash: 1_150_000 },
  { id: "2", name: "Vireon UK Ltd", currency: "GBP", revenue: 320000, expenses: 210000, cash: 280_000 },
  { id: "3", name: "Vireon Dubai FZ", currency: "AED", revenue: 450000, expenses: 280000, cash: 420_000 },
  { id: "4", name: "Vireon India Pvt Ltd", currency: "INR", revenue: 8_500_000, expenses: 5_200_000, cash: 12_000_000 },
];

const FX_RATES: Record<string, number> = { USD: 1, GBP: 1.27, EUR: 1.09, AED: 0.272, INR: 0.012, SGD: 0.74 };

const convertCurrency = (amount: number, fromCurrency: string, toCurrency: string) => {
  const fromUSD = FX_RATES[fromCurrency] || 1;
  const toUSD = FX_RATES[toCurrency] || 1;
  return (amount * fromUSD) / toUSD;
};

export default function ConsolidationPage() {
  
  const [loading, setLoading] = useState(false);
  const [entities, setEntities] = useState<Entity[]>(DEMO_ENTITIES);
  const [result, setResult] = useState<ConsolidationResult | null>(null);
  const [baseCurrency, setBaseCurrency] = useState("USD");
  const [period, setPeriod] = useState(new Date().toISOString().slice(0, 7));

  const consolidate = () => {
    setLoading(true);
    setTimeout(() => {
      const inBase = entities.map((e) => {
        return {
          ...e,
          revenue_base: convertCurrency(e.revenue, e.currency, baseCurrency),
          expenses_base: convertCurrency(e.expenses, e.currency, baseCurrency),
          cash_base: convertCurrency(e.cash, e.currency, baseCurrency),
        };
      });

      const totalRevenue = inBase.reduce((sum, e) => sum + e.revenue_base, 0);
      const totalExpenses = inBase.reduce((sum, e) => sum + e.expenses_base, 0);
      const totalCash = inBase.reduce((sum, e) => sum + e.cash_base, 0);
      const eliminations = totalRevenue * 0.04; // 4% typical interco elimination

      setResult({
        entities,
        consolidated: {
          total_revenue: totalRevenue - eliminations,
          total_expenses: totalExpenses,
          total_cash: totalCash,
          net_income: totalRevenue - eliminations - totalExpenses,
          entity_count: entities.length,
        },
        intercompany_eliminations: eliminations,
        fx_adjustments: Object.fromEntries(
          entities.map((e) => [e.name, convertCurrency(1, e.currency, baseCurrency)])
        ),
      });
      setLoading(false);
    }, 800);
  };

  const formatBase = (n: number) => {
    const symbols: Record<string, string> = { USD: "$", GBP: "£", EUR: "€", AED: "AED ", INR: "₹", SGD: "S$" };
    const sym = symbols[baseCurrency] || `${baseCurrency} `;
    return n >= 1_000_000 ? `${sym}${(n / 1_000_000).toFixed(2)}M` :
    n >= 1_000 ? `${sym}${(n / 1_000).toFixed(0)}K` : `${sym}${n.toFixed(0)}`;
  };

  const formatLocal = (n: number, currency: string) => {
    const symbols: Record<string, string> = { USD: "$", GBP: "£", EUR: "€", AED: "AED ", INR: "₹", SGD: "S$" };
    const sym = symbols[currency] || currency + " ";
    return `${sym}${n.toLocaleString()}`;
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#fdf9f4]">
      <TopBar title="Multi-Entity Consolidation" />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* Header */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-[#3d2c1e]">Multi-Entity Consolidation</h1>
            <p className="text-sm text-[#8c6a4a] mt-1">
              Consolidated P&L across entities with FX translation and intercompany elimination
            </p>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="month"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="text-sm border border-[#e3d6c7] rounded-lg px-3 py-2 bg-white text-[#3d2c1e] focus:outline-none"
            />
            <select
              value={baseCurrency}
              onChange={(e) => setBaseCurrency(e.target.value)}
              className="text-sm border border-[#e3d6c7] rounded-lg px-3 py-2 bg-white text-[#3d2c1e] focus:outline-none"
            >
              {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <button
              onClick={consolidate}
              disabled={loading}
              className={cn(
                "flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all shadow-sm",
                loading
                  ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                  : "bg-[#c8873a] text-white hover:bg-[#a86d2a] active:scale-95"
              )}
            >
              <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              {loading ? "Consolidating…" : "Consolidate"}
            </button>
          </div>
        </div>

        {/* Entity grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {entities.map((e) => {
            const rate = { USD: 1, GBP: 1.27, EUR: 1.09, AED: 0.272, INR: 0.012, SGD: 0.74 }[e.currency] || 1;
            return (
              <Card key={e.id} className="bg-white border border-[#e3d6c7] rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Building2 className="w-4 h-4 text-[#c8873a]" />
                  <span className="text-xs font-semibold text-[#3d2c1e] truncate">{e.name}</span>
                </div>
                <div className="space-y-1 text-xs text-[#8c6a4a]">
                  <div className="flex justify-between">
                    <span>Revenue</span>
                    <span className="font-semibold text-[#3d2c1e]">{formatLocal(e.revenue, e.currency)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Expenses</span>
                    <span className="font-semibold text-[#3d2c1e]">{formatLocal(e.expenses, e.currency)}</span>
                  </div>
                  <div className="flex justify-between border-t pt-1">
                    <span>Net Income</span>
                    <span className={cn("font-bold", (e.revenue - e.expenses) >= 0 ? "text-green-600" : "text-red-600")}>
                      {formatLocal(e.revenue - e.expenses, e.currency)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>USD rate</span>
                    <span className="text-[#c8873a] font-medium">{rate.toFixed(3)}</span>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>

        {/* Consolidated result */}
        {result && (
          <>
            <Card className="bg-white border border-[#e3d6c7] rounded-2xl p-5">
              <Title className="text-sm font-semibold text-[#3d2c1e] mb-4 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-[#c8873a]" />
                Consolidated P&L ({baseCurrency}) — {period}
              </Title>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {[
                  { label: "Total Revenue", value: formatBase(result.consolidated.total_revenue), color: "text-green-600" },
                  { label: "Total Expenses", value: formatBase(result.consolidated.total_expenses), color: "text-red-600" },
                  { label: "Net Income", value: formatBase(result.consolidated.net_income), color: result.consolidated.net_income >= 0 ? "text-green-600" : "text-red-600" },
                  { label: "Total Cash", value: formatBase(result.consolidated.total_cash), color: "text-blue-600" },
                  { label: "Interco Eliminations", value: formatBase(result.intercompany_eliminations), color: "text-amber-600" },
                ].map((kpi) => (
                  <div key={kpi.label} className="p-3 bg-[#fdf5ea] rounded-xl text-center">
                    <p className="text-xs text-[#8c6a4a] mb-1">{kpi.label}</p>
                    <p className={cn("text-lg font-bold", kpi.color)}>{kpi.value}</p>
                  </div>
                ))}
              </div>
            </Card>

            {/* FX adjustments */}
            <Card className="bg-white border border-[#e3d6c7] rounded-2xl p-5">
              <Title className="text-sm font-semibold text-[#3d2c1e] mb-3">FX Translation Rates Applied</Title>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(result.fx_adjustments).map(([entity, rate]) => (
                  <div key={entity} className="text-xs p-3 bg-[#fdf5ea] rounded-xl">
                    <p className="text-[#8c6a4a] truncate">{entity}</p>
                    <p className="font-semibold text-[#3d2c1e] mt-1">Rate: {rate.toFixed(4)} → {baseCurrency}</p>
                  </div>
                ))}
              </div>
            </Card>
          </>
        )}

        {!result && (
          <Card className="bg-white border border-[#e3d6c7] rounded-2xl p-8 text-center">
            <Building2 className="w-10 h-10 text-[#c8873a] mx-auto mb-3 opacity-60" />
            <p className="text-base font-semibold text-[#3d2c1e]">Consolidate Financials</p>
            <p className="text-sm text-[#8c6a4a] mt-1 max-w-sm mx-auto">
              Combine P&L across all entities with automatic FX translation and intercompany elimination.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
