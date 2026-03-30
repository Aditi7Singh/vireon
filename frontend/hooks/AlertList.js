import { Card, Title, Text, List, ListItem, Flex, Badge } from '@tremor/react';

const severityColors = {
  critical: 'red',
  warning: 'amber',
};

const SeverityBadge = ({ severity }) => (
    <Badge color={severityColors[severity] || 'gray'} className="capitalize">{severity}</Badge>
);

export default function AlertList({ alerts, isLoading }) {
  if (isLoading) {
    return (
        <Card>
            <Title>Active Financial Alerts</Title>
            <div className="animate-pulse mt-4 space-y-2">
                <div className="h-8 bg-slate-200 rounded w-full"></div>
                <div className="h-8 bg-slate-200 rounded w-4/5"></div>
                <div className="h-8 bg-slate-200 rounded w-full"></div>
            </div>
        </Card>
    );
  }

  if (!alerts || !alerts.alerts || alerts.alerts.length === 0) {
      return (
          <Card>
              <Title>Active Financial Alerts</Title>
              <Text className="mt-4 text-slate-500">No active alerts found. Your finances are looking clean!</Text>
          </Card>
      )
  }

  return (
    <Card>
      <Title>Active Financial Alerts ({alerts.total})</Title>
      <List className="mt-2">
        {alerts.alerts.map((alert) => (
          <ListItem key={alert.id}>
              <SeverityBadge severity={alert.severity} />
              <Text className="ml-3 truncate">{alert.description}</Text>
          </ListItem>
        ))}
      </List>
    </Card>
  );
}