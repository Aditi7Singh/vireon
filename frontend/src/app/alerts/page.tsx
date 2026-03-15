'use client';

import { useState, useMemo } from 'react';
import { useAlerts } from '@/hooks/useFinancialData';
import { useDismissAlert, useStreamingChat } from '@/hooks/useChat';
import { useAppStore } from '@/lib/store';
import { Alert } from '@/lib/api';
import { formatRelativeTime, formatCurrency, cn } from '@/lib/utils';
import {
  AlertCircle,
  AlertTriangle,
  Info,
  Cloud,
  Users,
  Package,
  Zap,
  TrendingUp,
  Send,
  Search,
} from 'lucide-react';

const CATEGORY_ICONS: Record<string, typeof Cloud> = {
  'AWS': Cloud,
  'Cloud Infrastructure': Cloud,
  'Payroll': Users,
  'Salaries': Users,
  'Vendors': Package,
  'Tools': Zap,
  'Software': Zap,
  'Revenue': TrendingUp,
};

type Tab = 'active' | 'resolved';
type FilterSeverity = 'all' | 'CRITICAL' | 'WARNING' | 'INFO';

export default function AlertsPage() {
  const { data: alertsData, isLoading } = useAlerts('', '', 100);
  const { dismissAlert } = useDismissAlert();
  const { sendMessage } = useStreamingChat();
  const { openChat } = useAppStore();

  const [tab, setTab] = useState<Tab>('active');
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<FilterSeverity>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set<string>();
    alertsData.alerts.forEach((a) => cats.add(a.category));
    return Array.from(cats).sort();
  }, [alertsData.alerts]);

  // Filter alerts
  const filteredAlerts = useMemo(() => {
    let alerts = alertsData.alerts;

    // Filter by tab
    if (tab === 'active') {
      alerts = alerts.filter((a) => !dismissed.has(a.id));
    } else {
      alerts = alerts.filter((a) => dismissed.has(a.id));
    }

    // Filter by severity
    if (severityFilter !== 'all') {
      alerts = alerts.filter((a) => a.severity === severityFilter);
    }

    // Filter by category
    if (categoryFilter !== 'all') {
      alerts = alerts.filter((a) => a.category === categoryFilter);
    }

    // Search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      alerts = alerts.filter(
        (a) =>
          a.description.toLowerCase().includes(query) ||
          a.category.toLowerCase().includes(query) ||
          a.alert_type.toLowerCase().includes(query)
      );
    }

    return alerts;
  }, [alertsData.alerts, tab, searchQuery, severityFilter, categoryFilter, dismissed]);

  // Separate critical and other
  const criticalAlerts = filteredAlerts.filter((a) => a.severity === 'CRITICAL');
  const otherAlerts = filteredAlerts.filter((a) => a.severity !== 'CRITICAL');
  const visibleAlerts = [...criticalAlerts, ...otherAlerts];

  const handleDismiss = async (alertId: string) => {
    setDismissed((prev) => new Set(prev).add(alertId));
    await dismissAlert(alertId);
  };

  const handleBulkDismiss = async () => {
    const toDismiss = filteredAlerts.filter((a) => !dismissed.has(a.id));
    for (const alert of toDismiss) {
      setDismissed((prev) => new Set(prev).add(alert.id));
      await dismissAlert(alert.id);
    }
  };

  const handleAskAI = async (alert: Alert) => {
    const message = `Explain the ${alert.category} anomaly and what I should do about it. Context: ${alert.description}`;
    await sendMessage(message);
    openChat();
  };

  const activeCount = alertsData.alerts.filter((a) => !dismissed.has(a.id)).length;
  const resolvedCount = alertsData.alerts.filter((a) => dismissed.has(a.id)).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Alerts</h1>
        <p className="text-cfo-muted mt-1">
          Manage and review all financial anomalies and alerts
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="p-4 rounded-lg bg-cfo-surface border border-cfo-border">
          <p className="text-xs text-cfo-muted mb-1">Total Alerts</p>
          <p className="text-2xl font-bold text-white">{alertsData.alerts.length}</p>
        </div>
        <div className="p-4 rounded-lg bg-red-500/5 border border-red-500/30">
          <p className="text-xs text-red-300 mb-1">Active</p>
          <p className="text-2xl font-bold text-red-400">{activeCount}</p>
        </div>
        <div className="p-4 rounded-lg bg-green-500/5 border border-green-500/30">
          <p className="text-xs text-green-300 mb-1">Resolved</p>
          <p className="text-2xl font-bold text-green-400">{resolvedCount}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-cfo-border">
        <button
          onClick={() => setTab('active')}
          className={cn(
            'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
            tab === 'active'
              ? 'border-cfo-accent text-cfo-accent'
              : 'border-transparent text-cfo-muted hover:text-white'
          )}
        >
          Active ({activeCount})
        </button>
        <button
          onClick={() => setTab('resolved')}
          className={cn(
            'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
            tab === 'resolved'
              ? 'border-cfo-accent text-cfo-accent'
              : 'border-transparent text-cfo-muted hover:text-white'
          )}
        >
          Resolved ({resolvedCount})
        </button>
      </div>

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Search */}
        <div className="md:col-span-2 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cfo-muted" />
          <input
            type="text"
            placeholder="Search alerts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg bg-cfo-surface border border-cfo-border text-white placeholder:text-cfo-muted focus:outline-none focus:ring-2 focus:ring-cfo-accent"
          />
        </div>

        {/* Severity Filter */}
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value as FilterSeverity)}
          className="px-4 py-2 rounded-lg bg-cfo-surface border border-cfo-border text-white focus:outline-none focus:ring-2 focus:ring-cfo-accent"
        >
          <option value="all">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="WARNING">Warning</option>
          <option value="INFO">Info</option>
        </select>

        {/* Category Filter */}
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-4 py-2 rounded-lg bg-cfo-surface border border-cfo-border text-white focus:outline-none focus:ring-2 focus:ring-cfo-accent"
        >
          <option value="all">All Categories</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>

      {/* Bulk Actions */}
      {tab === 'active' && visibleAlerts.length > 0 && (
        <div className="flex items-center justify-between p-4 rounded-lg bg-cfo-surface border border-cfo-border">
          <p className="text-sm text-cfo-muted">
            Showing <span className="font-semibold text-white">{visibleAlerts.length}</span> alert
            {visibleAlerts.length !== 1 ? 's' : ''}
          </p>
          <button
            onClick={handleBulkDismiss}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-cfo-accent text-black hover:bg-opacity-90 transition-colors"
          >
            Dismiss All
          </button>
        </div>
      )}

      {/* Empty State */}
      {visibleAlerts.length === 0 && (
        <div className="p-12 rounded-lg border border-cfo-border bg-gradient-to-br from-cfo-surface to-cfo-surface2 text-center">
          <AlertCircle className="w-12 h-12 text-cfo-muted mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-semibold text-white mb-2">
            {tab === 'active' ? 'No active alerts' : 'No resolved alerts'}
          </h3>
          <p className="text-sm text-cfo-muted">
            {tab === 'active'
              ? 'Great! All spending is within normal ranges.'
              : 'No alerts have been resolved yet.'}
          </p>
        </div>
      )}

      {/* Alert List */}
      <div className="space-y-3">
        {visibleAlerts.map((alert) => (
          <AlertCard
            key={alert.id}
            alert={alert}
            onDismiss={() => handleDismiss(alert.id)}
            onAskAI={() => handleAskAI(alert)}
            isDismissed={dismissed.has(alert.id)}
            isCritical={alert.severity === 'CRITICAL'}
          />
        ))}
      </div>
    </div>
  );
}

interface AlertCardProps {
  alert: Alert;
  onDismiss: () => void;
  onAskAI: () => void;
  isDismissed: boolean;
  isCritical: boolean;
}

function AlertCard({
  alert,
  onDismiss,
  onAskAI,
  isDismissed,
  isCritical,
}: AlertCardProps) {
  const getSeverityIcon = () => {
    switch (alert.severity) {
      case 'CRITICAL':
        return <AlertCircle className="w-5 h-5" />;
      case 'WARNING':
        return <AlertTriangle className="w-5 h-5" />;
      default:
        return <Info className="w-5 h-5" />;
    }
  };

  const getSeverityColor = () => {
    switch (alert.severity) {
      case 'CRITICAL':
        return 'border-l-4 border-red-500 bg-red-500/5';
      case 'WARNING':
        return 'border-l-4 border-yellow-500 bg-yellow-500/5';
      default:
        return 'border-l-4 border-blue-500 bg-blue-500/5';
    }
  };

  const getSeverityBadgeColor = () => {
    switch (alert.severity) {
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-300 border border-red-500/30';
      case 'WARNING':
        return 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30';
      default:
        return 'bg-blue-500/20 text-blue-300 border border-blue-500/30';
    }
  };

  const CategoryIcon = CATEGORY_ICONS[alert.category] || Package;

  return (
    <div
      className={cn(
        'p-5 rounded-lg border border-cfo-border transition-all duration-200',
        getSeverityColor(),
        isCritical && 'ring-1 ring-red-500/30',
        isDismissed && 'opacity-60'
      )}
    >
      {/* Header Row */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 flex-1">
          <div
            className={cn(
              'p-2 rounded-lg flex-shrink-0',
              alert.severity === 'CRITICAL'
                ? 'bg-red-500/20'
                : alert.severity === 'WARNING'
                  ? 'bg-yellow-500/20'
                  : 'bg-blue-500/20'
            )}
          >
            {getSeverityIcon()}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-semibold', getSeverityBadgeColor())}>
                {alert.severity}
              </span>
              <div className="flex items-center gap-1 text-cfo-muted">
                <CategoryIcon className="w-4 h-4" />
                <span className="text-xs font-medium">{alert.category}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Title */}
      <h3 className="font-semibold text-white mb-1 text-sm">{alert.alert_type}</h3>

      {/* Description */}
      <p className="text-sm text-cfo-muted mb-3">{alert.description}</p>

      {/* Details Grid */}
      <div className="grid grid-cols-4 gap-3 mb-4 p-3 bg-white/5 rounded-lg">
        {/* Amount */}
        {alert.amount !== null && (
          <div>
            <p className="text-xs text-cfo-muted mb-0.5">Amount</p>
            <p className="text-sm font-semibold text-white">{formatCurrency(alert.amount)}</p>
          </div>
        )}

        {/* Baseline */}
        {alert.baseline !== null && (
          <div>
            <p className="text-xs text-cfo-muted mb-0.5">Baseline</p>
            <p className="text-sm font-semibold text-white">{formatCurrency(alert.baseline)}</p>
          </div>
        )}

        {/* Delta % */}
        {alert.delta_pct !== null && (
          <div>
            <p className="text-xs text-cfo-muted mb-0.5">Change</p>
            <p className={cn('text-sm font-semibold', alert.delta_pct > 0 ? 'text-red-400' : 'text-green-400')}>
              {alert.delta_pct > 0 ? '+' : ''}{(alert.delta_pct * 100).toFixed(1)}%
            </p>
          </div>
        )}

        {/* Runway Impact */}
        {alert.runway_impact !== null && (
          <div>
            <p className="text-xs text-cfo-muted mb-0.5">Runway Impact</p>
            <p className={cn('text-sm font-semibold', alert.runway_impact < 0 ? 'text-red-400' : 'text-green-400')}>
              {alert.runway_impact < 0 ? '−' : '+'}{Math.abs(alert.runway_impact).toFixed(1)} months
            </p>
          </div>
        )}
      </div>

      {/* Owner & Timestamp */}
      <div className="flex items-center justify-between text-xs text-cfo-muted mb-4">
        <div>
          {alert.suggested_owner && (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-cfo-surface2 border border-cfo-border">
              Suggested owner: <span className="font-semibold text-white">{alert.suggested_owner}</span>
            </span>
          )}
        </div>
        <span>{formatRelativeTime(alert.created_at)}</span>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        {!isDismissed && (
          <>
            <button
              onClick={onAskAI}
              className={cn(
                'flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white hover:from-blue-500/30 hover:to-purple-500/30',
                'border border-blue-500/30 hover:border-blue-500/50',
                'flex items-center justify-center gap-2'
              )}
            >
              <Send className="w-4 h-4" />
              Ask AI
            </button>
            <button
              onClick={onDismiss}
              className={cn(
                'flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                'bg-cfo-surface2 text-cfo-muted hover:bg-cfo-border',
                'border border-cfo-border'
              )}
            >
              Dismiss
            </button>
          </>
        )}
        {isDismissed && (
          <div className="flex items-center justify-center w-full px-3 py-2 rounded-lg bg-cfo-surface2 text-cfo-muted text-sm border border-cfo-border">
            ✓ Dismissed
          </div>
        )}
      </div>
    </div>
  );
}
