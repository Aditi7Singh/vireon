'use client';

import { useState } from 'react';
import Link from 'next/link';
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
  X,
} from 'lucide-react';

interface Props {
  alerts?: Alert[];
  loading?: boolean;
}

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

export function AlertsFeed({ alerts: propAlerts, loading: propLoading }: Props) {
  const { data: alertsData, isLoading: defaultLoading } = useAlerts();
  const { dismissAlert } = useDismissAlert();
  const { sendMessage } = useStreamingChat();
  const { openChat } = useAppStore();
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const [isScanning, setIsScanning] = useState(false);

  const alerts = propAlerts ?? alertsData.alerts;
  const loading = propLoading ?? defaultLoading;

  // Separate critical and other alerts
  const criticalAlerts = alerts.filter((a) => a.severity === 'CRITICAL' && !dismissed.has(a.id));
  const otherAlerts = alerts.filter((a) => a.severity !== 'CRITICAL' && !dismissed.has(a.id));
  const visibleAlerts = [...criticalAlerts, ...otherAlerts];

  const handleDismiss = async (alertId: string) => {
    setDismissed((prev) => new Set(prev).add(alertId));
    await dismissAlert(alertId);
  };

  const handleAskAI = async (alert: Alert) => {
    const message = `Explain the ${alert.category} anomaly and what I should do about it. Context: ${alert.description}`;
    await sendMessage(message);
    openChat();
  };

  const handleScanNow = async () => {
    setIsScanning(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/alerts/scan-now`,
        { method: 'POST' }
      );
      // Optionally refetch alerts here
    } finally {
      setIsScanning(false);
    }
  };

  if (loading && visibleAlerts.length === 0) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="p-6 rounded-lg bg-cfo-surface border border-cfo-border animate-pulse"
          >
            <div className="h-24 bg-cfo-surface2 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (visibleAlerts.length === 0) {
    return (
      <div className="p-8 rounded-lg border border-cfo-border bg-gradient-to-br from-cfo-surface to-cfo-surface2 text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-500/10 mb-4">
          <AlertCircle className="w-6 h-6 text-green-400" />
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">No active alerts</h3>
        <p className="text-sm text-cfo-muted">All spending is within normal ranges</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">
            Active Alerts ({visibleAlerts.length})
          </h2>
          <p className="text-xs text-cfo-muted mt-1">
            {criticalAlerts.length} critical, {otherAlerts.length} other
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleScanNow}
            disabled={isScanning}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-cfo-accent text-black hover:bg-opacity-90 disabled:opacity-50 transition-all"
          >
            {isScanning ? 'Scanning...' : 'Scan Now'}
          </button>
          <Link
            href="/alerts"
            className="px-4 py-2 text-sm font-medium rounded-lg bg-cfo-surface2 text-cfo-accent hover:bg-cfo-border transition-colors"
          >
            View All →
          </Link>
        </div>
      </div>

      {/* Alert Cards */}
      <div className="space-y-3">
        {visibleAlerts.map((alert) => (
          <AlertCard
            key={alert.id}
            alert={alert}
            onDismiss={() => handleDismiss(alert.id)}
            onAskAI={() => handleAskAI(alert)}
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
  isCritical: boolean;
}

function AlertCard({ alert, onDismiss, onAskAI, isCritical }: AlertCardProps) {
  const [isHovering, setIsHovering] = useState(false);

  // Get severity icon and colors
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

  // Get category icon
  const CategoryIcon = CATEGORY_ICONS[alert.category] || Package;

  return (
    <div
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      className={cn(
        'p-5 rounded-lg border border-cfo-border transition-all duration-200',
        getSeverityColor(),
        isCritical && 'ring-1 ring-red-500/30'
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

        {/* Close Button */}
        <button
          onClick={onDismiss}
          className="p-1 hover:bg-white/10 rounded transition-colors flex-shrink-0 opacity-0 group-hover:opacity-100"
        >
          <X className="w-4 h-4 text-cfo-muted" />
        </button>
      </div>

      {/* Title */}
      <h3 className="font-semibold text-white mb-1 text-sm">{alert.alert_type}</h3>

      {/* Description */}
      <p className="text-sm text-cfo-muted mb-3">{alert.description}</p>

      {/* Details Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4 p-3 bg-white/5 rounded-lg">
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
        <div className="">
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
      </div>
    </div>
  );
}

