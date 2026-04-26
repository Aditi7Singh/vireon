import { Card, Grid, Title, Text, Col } from '@tremor/react';
import Header from '../components/layout/Header';
import { useScorecard, useAlerts, useRunway, useRevenue } from '../hooks/useFinancialData';
import AlertList from '../components/dashboard/AlertList';
import KpiCard from '../components/dashboard/KpiCard';

export default function DashboardPage() {
  const { scorecard, isLoading: scorecardLoading } = useScorecard();
  const { alerts, isLoading: alertsLoading } = useAlerts();

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return null;
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(value);
  }

  return (
    <main className="bg-slate-50 min-h-screen">
      <Header />
      <div className="p-4 sm:p-6 lg:p-8">
        <Title>Financial Overview</Title>
        <Text>Real-time financial command center for your startup.</Text>

        <Grid numItemsSm={2} numItemsLg={4} className="gap-6 mt-6">
          <KpiCard title="Total Cash" metric={formatCurrency(scorecard?.total_cash)} isLoading={scorecardLoading} />
          <KpiCard title="Cash Runway" metric={scorecard?.runway_months} unit="months" isLoading={scorecardLoading} />
          <KpiCard title="Net Burn (30d)" metric={formatCurrency(scorecard?.monthly_net_burn)} isLoading={scorecardLoading} />
          <KpiCard title="ARR" metric={formatCurrency(scorecard?.arr)} isLoading={scorecardLoading} />
        </Grid>

        <div className="mt-6">
            <AlertList alerts={alerts} isLoading={alertsLoading} />
        </div>
      </div>
    </main>
  );
}