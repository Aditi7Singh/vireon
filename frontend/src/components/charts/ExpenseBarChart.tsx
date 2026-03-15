'use client';

import { useMemo, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { useExpenses, useAlerts } from '@/hooks/useFinancialData';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { AlertCircle } from 'lucide-react';

interface ChartData {
  month: string;
  [key: string]: string | number | undefined;
}

type Period = '3M' | '6M' | '12M';

const CATEGORY_COLORS = {
  'Salaries': '#4ade80',
  'Cloud Infrastructure': '#60a5fa',
  'Marketing': '#818cf8',
  'Office': '#f59e0b',
  'Tools & Software': '#f87171',
  'Other': '#6b7280',
};

export function ExpenseBarChart() {
  const [period, setPeriod] = useState<Period>('3M');
  const { data: expenseData, isLoading: expensesLoading } = useExpenses(
    period === '3M' ? 3 : period === '6M' ? 6 : 12
  );
  const { data: alertsData } = useAlerts('CRITICAL', 'expenses', 50);

  // Build map of categories with CRITICAL alerts
  const criticalCategories = useMemo(() => {
    const map = new Set<string>();
    (alertsData?.alerts || []).forEach((alert) => {
      if (alert.severity === 'CRITICAL' && alert.category) {
        map.add(alert.category);
      }
    });
    return map;
  }, [alertsData]);

  const chartData = useMemo(() => {
    if (!expenseData?.breakdown) return [];

    // Get top 6 categories by total amount
    const categories = Object.entries(expenseData.breakdown)
      .sort(([, a], [, b]) => (b as number) - (a as number))
      .slice(0, 6)
      .map(([cat]) => cat);

    // Build monthly breakdown if trend data exists
    if (expenseData.trend && Object.keys(expenseData.trend).length > 0) {
      const months: ChartData[] = [];
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const now = new Date();

      const dataPoints = period === '3M' ? 3 : period === '6M' ? 6 : 12;
      for (let i = dataPoints - 1; i >= 0; i--) {
        const date = new Date(now);
        date.setMonth(date.getMonth() - i);
        const monthLabel = monthNames[date.getMonth()];

        const row: ChartData = { month: monthLabel };
        categories.forEach((cat) => {
          const monthTrend = (expenseData.trend[cat] as number[] | undefined) || [];
          row[cat] = monthTrend[i] || 0;
        });
        months.push(row);
      }
      return months;
    }

    // Fallback: show categories as single bar
    const row: ChartData = { month: 'Current' };
    categories.forEach((cat) => {
      row[cat] = (expenseData.breakdown[cat] as number) || 0;
    });
    return [row];
  }, [expenseData, period]);

  if (expensesLoading) {
    return (
      <div className="p-6 rounded-lg border border-cfo-border bg-cfo-surface h-96 animate-pulse">
        <div className="h-full bg-cfo-surface2 rounded" />
      </div>
    );
  }

  return (
    <div className="p-6 rounded-lg border border-cfo-border bg-cfo-surface">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white">Expenses by Category</h2>
        <div className="flex gap-2">
          {(['3M', '6M', '12M'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={cn(
                'px-3 py-1 text-xs font-medium rounded transition-colors',
                period === p
                  ? 'bg-cfo-accent text-black'
                  : 'bg-cfo-surface2 text-cfo-muted hover:bg-cfo-border'
              )}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Legend with anomaly indicator */}
      {criticalCategories.size > 0 && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400" />
          <p className="text-xs text-red-200">
            {criticalCategories.size} categor{criticalCategories.size === 1 ? 'y' : 'ies'} with active abnormal spending
          </p>
        </div>
      )}

      {/* Chart */}
      <div style={{ width: '100%', height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
            <XAxis dataKey="month" stroke="#718096" />
            <YAxis 
              stroke="#718096"
              tickFormatter={(value) => {
                if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
                if (value >= 1000) return `$${(value / 1000).toFixed(0)}k`;
                return `$${value}`;
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a202c',
                border: '1px solid #2d3748',
                borderRadius: '0.5rem',
              }}
              formatter={(value: number | string) => {
                if (typeof value === 'number') {
                  return formatCurrency(value);
                }
                return value;
              }}
            />
            <Legend />
            {Object.keys(CATEGORY_COLORS).slice(0, 6).map((category, idx) => (
              <Bar 
                key={idx}
                dataKey={category}
                stackId="expenses"
                fill={CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS]}
                name={category}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Anomaly Details */}
      {criticalCategories.size > 0 && (
        <div className="mt-4 p-3 bg-cfo-surface2 rounded-lg">
          <p className="text-xs text-cfo-muted mb-2">Abnormal Spending Detected:</p>
          <div className="space-y-1">
            {Array.from(criticalCategories).map((cat) => (
              <div key={cat} className="text-xs text-red-400 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-400" />
                {cat}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
