import { Card, Text, Metric } from '@tremor/react';

export default function KpiCard({ title, metric, unit, isLoading }) {
  
  const displayMetric = () => {
    if (isLoading) return '...';
    if (metric === null || metric === undefined) return 'N/A';
    return unit ? `${metric} ${unit}` : metric;
  }

  return (
    <Card>
      <Text>{title}</Text>
      <Metric className={isLoading ? 'text-transparent bg-slate-200 animate-pulse rounded-md' : ''}>
        {
          // This trick prevents layout shift while loading
          isLoading ? 'Loading' : displayMetric()
        }
      </Metric>
    </Card>
  );
}