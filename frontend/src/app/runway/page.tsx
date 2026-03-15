'use client';

import { useState, useMemo } from 'react';
import useSWR from 'swr';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { AlertCircle, RefreshCw, Settings2 } from 'lucide-react';
import { formatCurrency, cn } from '@/lib/utils';
import { Runway, BurnRate, ExpenseBreakdown } from '@/lib/api';
import { RunwayAreaChart } from '@/components/charts/RunwayAreaChart';
import { ScenarioModal } from '@/components/scenarios/ScenarioModal';

type ScenarioType = 'current' | 'optimistic' | 'pessimistic';

interface ScenarioResult {
  name: string;
  runway: number;
  delta: number;
  zeroDate: string | Date;
  type: ScenarioType;
}

interface PreComputedScenario {
  name: string;
  runway: number;
  delta: number;
  zeroDates: string;
  scenarioType?: 'hire' | 'expense' | 'revenue' | 'churn';
  prefilledParams?: Record<string, string | number | boolean | undefined>;
}

export default function RunwayPage() {
  const [activeScenario, setActiveScenario] = useState<ScenarioType>('current');
  const [selectedExpenseCategory, setSelectedExpenseCategory] = useState<string | null>(null);
  const [scenarioModalOpen, setScenarioModalOpen] = useState(false);
  const [categoryTrendData, setCategoryTrendData] = useState<Array<{month: string; amount: number}>>([]);

  // Fetch runway data
  const { data: runwayData, isLoading: runwayLoading } = useSWR<Runway>('/api/metrics/runway');

  // Fetch burn rate data
  const { data: burnData, isLoading: burnLoading } = useSWR<BurnRate>('/api/metrics/burn-rate');

  // Fetch expense breakdown
  const { data: expenseData, isLoading: expenseLoading } = useSWR<ExpenseBreakdown>('/api/metrics/expenses');

  // Calculate scenario projections
  const scenarios = useMemo(() => {
    if (!runwayData || !burnData) return [];

    const baseRunway = runwayData.runway_months;
    const baseBurn = burnData.monthly_burn;

    // Optimistic: +20% revenue reduces burn by 20%
    const optimisticBurn = baseBurn * 0.8;
    const optRunway = (runwayData.cash_available / optimisticBurn);

    // Pessimistic: +10% burn
    const pessimisticBurn = baseBurn * 1.1;
    const pessRunway = (runwayData.cash_available / pessimisticBurn);

    return [
      {
        name: 'Current',
        runway: baseRunway,
        zeroDate: runwayData.zero_date,
        type: 'current' as ScenarioType,
      },
      {
        name: 'Optimistic (+20% Revenue)',
        runway: optRunway,
        zeroDate: addMonthsToDate(new Date(), optRunway),
        type: 'optimistic' as ScenarioType,
      },
      {
        name: 'Pessimistic (+10% Burn)',
        runway: pessRunway,
        zeroDate: addMonthsToDate(new Date(), pessRunway),
        type: 'pessimistic' as ScenarioType,
      },
    ];
  }, [runwayData, burnData]);

  // Pre-computed scenario table data
  const scenarioTableData: PreComputedScenario[] = useMemo(() => {
    if (!runwayData || !burnData) return [];

    const currentRunway = runwayData.runway_months;
    const currentZero = new Date(runwayData.zero_date);

    return [
      {
        name: 'Current trajectory',
        runway: currentRunway,
        delta: 0,
        zeroDates: currentZero.toLocaleDateString('en-US', {
          month: 'short',
          year: 'numeric',
        }),
      },
      {
        name: 'Hire 2 engineers ($120k avg)',
        runway: currentRunway - (2 * 120000) / 12 / burnData.monthly_burn,
        delta: -(2 * 120000) / 12 / burnData.monthly_burn,
        zeroDates: addMonthsToDate(new Date(), currentRunway - (2 * 120000) / 12 / burnData.monthly_burn).toLocaleDateString(
          'en-US',
          { month: 'short', year: 'numeric' }
        ),
        scenarioType: 'hire',
        prefilledParams: { engineers: 2, salary: 120000 },
      },
      {
        name: 'Cut AWS 30%',
        runway: currentRunway + (burnData.monthly_burn * 0.25 * 0.3) / burnData.monthly_burn,
        delta: (burnData.monthly_burn * 0.25 * 0.3) / burnData.monthly_burn,
        zeroDates: addMonthsToDate(
          new Date(),
          currentRunway + (burnData.monthly_burn * 0.25 * 0.3) / burnData.monthly_burn
        ).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
        scenarioType: 'expense',
        prefilledParams: { category: 'aws', reduction: 30 },
      },
      {
        name: 'Close $50K MRR deal',
        runway: currentRunway + 50000 / burnData.monthly_burn,
        delta: 50000 / burnData.monthly_burn,
        zeroDates: addMonthsToDate(new Date(), currentRunway + 50000 / burnData.monthly_burn).toLocaleDateString(
          'en-US',
          { month: 'short', year: 'numeric' }
        ),
        scenarioType: 'revenue',
        prefilledParams: { mrrDelta: 50000, probability: 100 },
      },
      {
        name: '10% customer churn',
        runway: currentRunway - 0.1 * (burnData.monthly_burn * 0.1) / burnData.monthly_burn,
        delta: -0.1 * (burnData.monthly_burn * 0.1) / burnData.monthly_burn,
        zeroDates: addMonthsToDate(
          new Date(),
          currentRunway - 0.1 * (burnData.monthly_burn * 0.1) / burnData.monthly_burn
        ).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
        scenarioType: 'churn',
        prefilledParams: { mrrDelta: -10000, probability: 100 },
      },
    ];
  }, [runwayData, burnData]);

  // Burn rate breakdown chart data
  const burnChartData = useMemo(() => {
    if (!expenseData) return [];
    return Object.entries(expenseData.breakdown).map(([category, amount]) => ({
      name: category,
      value: amount as number,
      percentage: ((amount as number) / expenseData.total) * 100,
    }));
  }, [expenseData]);

  const handleCategoryClick = (category: string) => {
    setSelectedExpenseCategory(category);
    // Generate trend data (mock)
    const mockTrendData = Array.from({ length: 12 }, (_, i) => ({
      month: new Date(new Date().setMonth(new Date().getMonth() - 11 + i))
        .toLocaleDateString('en-US', { month: 'short' })
        .toUpperCase(),
      amount: Math.random() * 50000 + 10000,
    }));
    setCategoryTrendData(mockTrendData);
  };

  const lastUpdated = useMemo(() => {
    if (!runwayData?.last_updated) return 'Unknown';
    const date = new Date(runwayData.last_updated);
    const now = new Date();
    const minutesAgo = Math.floor((now.getTime() - date.getTime()) / 60000);
    return minutesAgo === 0 ? 'Just now' : `${minutesAgo} minute${minutesAgo !== 1 ? 's' : ''} ago`;
  }, [runwayData]);

  if (runwayLoading || !runwayData) {
    return (
      <div className="min-h-screen bg-cfo-background p-8">
        <div className="max-w-4xl mx-auto">
          <div className="h-96 bg-cfo-surface border border-cfo-border rounded-lg animate-pulse" />
        </div>
      </div>
    );
  }

  const currentScenario = scenarios.find((s) => s.type === activeScenario);

  return (
    <div className="min-h-screen bg-cfo-background p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* SECTION 1: Runway Summary Header */}
        <div className="space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-5xl font-black text-white mb-2">
                {runwayData.runway_months.toFixed(1)}
              </h1>
              <p className="text-lg text-cfo-muted">months of runway</p>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="p-2 rounded hover:bg-cfo-surface2 transition text-cfo-muted hover:text-white"
              title="Refresh data"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>

          {/* Alert banner */}
          {runwayData.runway_months < 9 && (
            <div
              className={cn(
                'flex items-center gap-3 p-4 rounded-lg border',
                runwayData.runway_months < 6
                  ? 'bg-red-900/20 border-red-700'
                  : 'bg-amber-900/20 border-amber-700'
              )}
            >
              <AlertCircle
                className={cn(
                  'w-5 h-5 flex-shrink-0',
                  runwayData.runway_months < 6 ? 'text-red-500' : 'text-amber-500'
                )}
              />
              <span
                className={cn(
                  'text-sm',
                  runwayData.runway_months < 6 ? 'text-red-200' : 'text-amber-200'
                )}
              >
                {runwayData.runway_months < 6
                  ? '🚨 CRITICAL: Less than 6 months of runway. Immediate action required.'
                  : '⚠️ WARNING: Less than 9 months of runway. Review burn forecasts.'}
              </span>
            </div>
          )}

          {/* Zero date and confidence */}
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-cfo-surface border border-cfo-border rounded-lg">
              <p className="text-xs text-cfo-muted mb-1">Zero Date</p>
              <p className="text-lg font-semibold text-white">
                {new Date(runwayData.zero_date).toLocaleDateString('en-US', {
                  weekday: 'short',
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </p>
            </div>
            <div className="p-4 bg-cfo-surface border border-cfo-border rounded-lg">
              <p className="text-xs text-cfo-muted mb-1">Confidence Interval</p>
              <p className="text-lg font-semibold text-white">
                ±{runwayData.confidence_interval?.high || 1} weeks
              </p>
            </div>
            <div className="p-4 bg-cfo-surface border border-cfo-border rounded-lg">
              <p className="text-xs text-cfo-muted mb-1">Last Updated</p>
              <p className="text-sm text-white">{lastUpdated}</p>
            </div>
          </div>
        </div>

        {/* SECTION 2: Runway Trend Chart with Scenarios */}
        <div className="space-y-4">
          <div>
            <h2 className="text-2xl font-bold text-white mb-4">24-Month Runway Projection</h2>
          </div>

          {/* Scenario toggles */}
          <div className="flex gap-2">
            {scenarios.map((scenario) => (
              <button
                key={scenario.type}
                onClick={() => setActiveScenario(scenario.type)}
                className={cn(
                  'px-4 py-2 rounded-lg font-medium transition',
                  activeScenario === scenario.type
                    ? 'bg-cfo-accent text-black'
                    : 'bg-cfo-surface border border-cfo-border text-white hover:border-cfo-accent'
                )}
              >
                {scenario.name}
              </button>
            ))}
          </div>

          {/* Chart */}
          <div className="p-6 bg-cfo-surface border border-cfo-border rounded-lg">
            <RunwayAreaChart data={runwayData} />
          </div>

          {/* Scenario summary */}
          {currentScenario && (
            <div className="p-4 bg-cfo-surface2 border border-cfo-border rounded-lg">
              <p className="text-sm text-cfo-muted mb-2">{currentScenario.name}</p>
              <p className="text-2xl font-bold text-white">
                {currentScenario.runway.toFixed(1)} months •{' '}
                <span className="text-cfo-muted text-lg">
                  {typeof currentScenario.zeroDate === 'string'
                    ? new Date(currentScenario.zeroDate).toLocaleDateString('en-US', {
                        month: 'short',
                        year: 'numeric',
                      })
                    : currentScenario.zeroDate.toLocaleDateString('en-US', {
                        month: 'short',
                        year: 'numeric',
                      })}
                </span>
              </p>
            </div>
          )}
        </div>

        {/* SECTION 3: Burn Rate Breakdown */}
        {expenseData && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white">Burn Rate Breakdown</h2>

            {selectedExpenseCategory ? (
              // Category trend drawer
              <div className="p-6 bg-cfo-surface border border-cfo-border rounded-lg space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white capitalize">{selectedExpenseCategory} Trend</h3>
                  <button
                    onClick={() => setSelectedExpenseCategory(null)}
                    className="text-sm text-cfo-muted hover:text-white"
                  >
                    ✕ Close
                  </button>
                </div>

                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={categoryTrendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="month" stroke="#666" />
                    <YAxis stroke="#666" tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(val) => formatCurrency(val as number)} />
                    <Area type="monotone" dataKey="amount" stroke="#10b981" fill="#10b9811a" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              // Donut chart
              <div className="grid grid-cols-2 gap-6">
                <div className="p-6 bg-cfo-surface border border-cfo-border rounded-lg">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={burnChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={80}
                        outerRadius={120}
                        paddingAngle={1}
                        dataKey="value"
                        label={({ name, percentage }) => `${name} ${percentage.toFixed(0)}%`}
                      >
                        {burnChartData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={['#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'][index % 5]}
                          />
                        ))}
                      </Pie>
                      <Tooltip formatter={(val) => formatCurrency(val as number)} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="p-6 bg-cfo-surface border border-cfo-border rounded-lg space-y-3">
                  <p className="text-sm text-cfo-muted mb-4">Click a category to view 12-month trend</p>
                  {burnChartData.map((item) => (
                    <button
                      key={item.name}
                      onClick={() => handleCategoryClick(item.name)}
                      className="w-full text-left p-3 rounded hover:bg-cfo-surface2 transition group"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-white group-hover:text-cfo-accent capitalize">
                          {item.name}
                        </span>
                        <span className="text-cfo-muted group-hover:text-white">→</span>
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-sm text-cfo-muted">{formatCurrency(item.value)}</span>
                        <span className="text-xs text-cfo-muted">{item.percentage.toFixed(1)}% of burn</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* SECTION 4: Runway Scenario Table */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-white">Pre-Computed Scenarios</h2>

          <div className="overflow-x-auto border border-cfo-border rounded-lg">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-cfo-border bg-cfo-surface2">
                  <th className="px-6 py-3 text-left font-semibold text-white">Scenario</th>
                  <th className="px-6 py-3 text-right font-semibold text-white">Runway</th>
                  <th className="px-6 py-3 text-right font-semibold text-white">Delta</th>
                  <th className="px-6 py-3 text-right font-semibold text-white">Zero Date</th>
                  <th className="px-6 py-3 text-right font-semibold text-white">Action</th>
                </tr>
              </thead>
              <tbody>
                {scenarioTableData.map((scenario, idx) => (
                  <tr
                    key={idx}
                    className={cn(
                      'border-b border-cfo-border',
                      idx % 2 === 0 ? 'bg-cfo-surface' : 'bg-cfo-surface2/50'
                    )}
                  >
                    <td className="px-6 py-4 font-medium text-white">{scenario.name}</td>
                    <td className="px-6 py-4 text-right text-white">{scenario.runway.toFixed(1)} mo</td>
                    <td
                      className={cn(
                        'px-6 py-4 text-right font-semibold',
                        scenario.delta > 0
                          ? 'text-green-400'
                          : scenario.delta < 0
                            ? 'text-red-400'
                            : 'text-cfo-muted'
                      )}
                    >
                      {scenario.delta > 0 ? '+' : ''}{scenario.delta.toFixed(1)} mo
                    </td>
                    <td className="px-6 py-4 text-right text-cfo-muted">{scenario.zeroDates}</td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => setScenarioModalOpen(true)}
                        className="px-3 py-1 rounded text-sm bg-cfo-accent hover:bg-cfo-accent/90 text-black font-medium transition"
                      >
                        Simulate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* SECTION 5: Alert Thresholds Config */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-white">Alert Thresholds</h2>

          <div className="grid grid-cols-3 gap-4">
            <div className="p-6 bg-red-900/10 border border-red-700 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <p className="font-semibold text-red-200">Critical Alert</p>
                <span className="text-2xl font-bold text-red-400">&lt; 6</span>
              </div>
              <p className="text-sm text-red-300">months remaining</p>
            </div>

            <div className="p-6 bg-amber-900/10 border border-amber-700 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <p className="font-semibold text-amber-200">Warning Alert</p>
                <span className="text-2xl font-bold text-amber-400">&lt; 9</span>
              </div>
              <p className="text-sm text-amber-300">months remaining</p>
            </div>

            <div className="p-6 bg-blue-900/10 border border-blue-700 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <p className="font-semibold text-blue-200">Monitor</p>
                <span className="text-2xl font-bold text-blue-400">&lt; 12</span>
              </div>
              <p className="text-sm text-blue-300">months remaining</p>
            </div>
          </div>

          <div className="p-4 bg-cfo-surface2 border border-cfo-border rounded-lg flex items-center justify-between">
            <p className="text-sm text-cfo-muted">Custom threshold configuration</p>
            <button
              disabled
              className="px-4 py-2 rounded flex items-center gap-2 bg-cfo-surface border border-cfo-border text-cfo-muted cursor-not-allowed opacity-50"
              title="Coming soon"
            >
              <Settings2 className="w-4 h-4" />
              Edit
            </button>
          </div>
        </div>

        {/* Scenario Modal */}
        {runwayData && (
          <ScenarioModal
            open={scenarioModalOpen}
            onOpenChange={setScenarioModalOpen}
            currentRunway={runwayData.runway_months}
            currentBurn={burnData?.monthly_burn || 50000}
            currentMrr={100000}
          />
        )}
      </div>
    </div>
  );
}

// Helper function to add months to a date
function addMonthsToDate(date: Date, months: number): Date {
  const result = new Date(date);
  result.setMonth(result.getMonth() + Math.floor(months));
  result.setDate(result.getDate() + Math.round((months % 1) * 30));
  return result;
}
