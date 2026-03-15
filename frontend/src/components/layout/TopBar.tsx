'use client';

import { useState } from 'react';
import { useAppStore } from '@/lib/store';
import { useAlerts } from '@/hooks/useFinancialData';
import { API } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Bell, Clock, RefreshCw } from 'lucide-react';

export function TopBar() {
  const { lastSyncTime, activePage, setLastSyncTime } = useAppStore();
  const { data: alertsData, mutate: mutateAlerts } = useAlerts();
  const [scanning, setScanning] = useState(false);

  const alertCount = alertsData?.total || 0;
  const criticalCount = alertsData?.critical_count || 0;

  const getPageTitle = () => {
    const titles: Record<string, string> = {
      dashboard: 'Financial Dashboard',
      runway: 'Cash Runway',
      expenses: 'Expenses',
      revenue: 'Revenue',
      alerts: 'Alerts',
    };
    return titles[activePage] || 'Dashboard';
  };

  const formatTimeAgo = (date: Date | null) => {
    if (!date) return 'Never';
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  const handleScanNow = async () => {
    setScanning(true);
    try {
      const response = await API.scanNow();
      if (response) {
        // Poll for results
        let attempts = 0;
        while (attempts < 120) {
          await new Promise((r) => setTimeout(r, 500));
          const status = await API.getScanStatus(response.task_id);
          if (status?.status === 'success' || status?.status === 'failure') {
            // Revalidate alerts
            mutateAlerts();
            setLastSyncTime(new Date());
            break;
          }
          attempts++;
        }
      }
    } finally {
      setScanning(false);
    }
  };

  return (
    <header className="bg-[#111318] border-b border-cfo-border px-6 py-4 flex items-center justify-between">
      {/* Left: Page Title */}
      <h1 className="text-xl font-bold text-white">{getPageTitle()}</h1>

      {/* Right: Controls */}
      <div className="flex items-center gap-4">
        {/* Last Sync */}
        <div className="flex items-center gap-2 text-sm text-cfo-muted">
          <Clock size={16} />
          <span>Last synced: {formatTimeAgo(lastSyncTime)}</span>
        </div>

        {/* Alert Badge */}
        {alertCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-900/20 border border-red-500/30">
            <Bell size={16} className="text-red-400" />
            <span className="text-sm text-red-300 font-medium">
              {criticalCount > 0 ? `${criticalCount} critical` : `${alertCount} alerts`}
            </span>
          </div>
        )}

        {/* Scan Now Button */}
        <button
          onClick={handleScanNow}
          disabled={scanning}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 text-sm',
            scanning
              ? 'bg-cfo-accent/50 text-black cursor-not-allowed'
              : 'bg-cfo-accent text-black hover:bg-opacity-90'
          )}
        >
          <RefreshCw size={16} className={cn(scanning && 'animate-spin')} />
          {scanning ? 'Scanning...' : 'Scan Now'}
        </button>
      </div>
    </header>
  );
}
