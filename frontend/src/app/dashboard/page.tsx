'use client';

import { useCashBalance, useRunway, useBurnRate, useRevenue, useAlerts } from '@/hooks/useFinancialData';
import { RunwayCard } from '@/components/kpi/RunwayCard';
import { CashCard } from '@/components/kpi/CashCard';
import { BurnCard } from '@/components/kpi/BurnCard';
import { MrrCard } from '@/components/kpi/MrrCard';
import { RunwayAreaChart } from '@/components/charts/RunwayAreaChart';
import { ExpenseBarChart } from '@/components/charts/ExpenseBarChart';
import { RevenueLineChart } from '@/components/charts/RevenueLineChart';
import { AlertsFeed } from '@/components/alerts/AlertsFeed';

export default function DashboardPage() {
  const { data: cashData, isLoading: cashLoading } = useCashBalance();
  const { data: runwayData, isLoading: runwayLoading } = useRunway();
  const { data: burnData, isLoading: burnLoading } = useBurnRate();
  const { data: revenueData, isLoading: revenueLoading } = useRevenue();
  const { data: alertsData, isLoading: alertsLoading } = useAlerts();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-cfo-muted mt-1">Financial overview and key metrics</p>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <RunwayCard data={runwayData} loading={runwayLoading} />
        <CashCard data={cashData} loading={cashLoading} />
        <BurnCard data={burnData} loading={burnLoading} />
        <MrrCard data={revenueData} loading={revenueLoading} />
      </div>

      {/* Charts Row */}
      <div className="space-y-6">
        <RunwayAreaChart data={runwayData} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ExpenseBarChart />
          <RevenueLineChart />
        </div>
      </div>

      {/* Alerts Feed */}
      <AlertsFeed alerts={alertsData.alerts} loading={alertsLoading} />
    </div>
  );
}
