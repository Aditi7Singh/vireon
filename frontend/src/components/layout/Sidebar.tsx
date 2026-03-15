'use client';

import Link from 'next/link';
import { useAppStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  TrendingDown,
  Receipt,
  BarChart2,
  AlertCircle,
  MessageSquare,
} from 'lucide-react';

export function Sidebar() {
  const { sidebarExpanded, toggleSidebar, activePage, setActivePage, alertCount, openChat } =
    useAppStore();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
    { id: 'runway', label: 'Runway', icon: TrendingDown, href: '/runway' },
    { id: 'expenses', label: 'Expenses', icon: Receipt, href: '/expenses' },
    { id: 'revenue', label: 'Revenue', icon: BarChart2, href: '/revenue' },
    { id: 'alerts', label: 'Alerts', icon: AlertCircle, href: '/alerts' },
  ] as const;

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-screen bg-[#0e1117] border-r border-cfo-border transition-all duration-300 flex flex-col z-40',
        sidebarExpanded ? 'w-[220px]' : 'w-16'
      )}
    >
      {/* Logo Section */}
      <div className="h-16 border-b border-cfo-border flex items-center justify-center">
        <div className="flex items-center gap-2">
          {sidebarExpanded && (
            <div className="flex flex-col">
              <span className="text-xs font-bold text-cfo-accent">SeedlingLabs</span>
              <span className="text-xs text-cfo-muted">AI CFO</span>
            </div>
          )}
          {!sidebarExpanded && (
            <div className="w-8 h-8 rounded-full bg-cfo-accent flex items-center justify-center text-black font-bold text-sm">
              S
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          const hasAlerts = item.id === 'alerts' && alertCount > 0;

          return (
            <div key={item.id} className="relative">
              <Link
                href={item.href}
                onClick={() => setActivePage(item.id)}
                className={cn(
                  'flex items-center justify-center md:justify-start gap-3 px-3 py-3 rounded-lg transition-all duration-200 relative group',
                  isActive
                    ? 'text-cfo-accent'
                    : 'text-cfo-muted hover:text-white'
                )}
              >
                {/* Left border for active */}
                {isActive && (
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-cfo-accent rounded-r" />
                )}

                <Icon size={20} />

                {sidebarExpanded && (
                  <>
                    <span className="text-sm font-medium">{item.label}</span>
                    {hasAlerts && (
                      <span className="absolute right-2 top-1 w-2 h-2 bg-red-500 rounded-full" />
                    )}
                  </>
                )}

                {/* Alert badge on collapsed view */}
                {!sidebarExpanded && hasAlerts && (
                  <span className="absolute -right-1 -top-1 w-3 h-3 bg-red-500 rounded-full" />
                )}
              </Link>
            </div>
          );
        })}
      </nav>

      {/* Footer - AI CFO Button */}
      <div className="border-t border-cfo-border p-3">
        <button
          onClick={openChat}
          className={cn(
            'w-full flex items-center justify-center md:justify-start gap-2 px-3 py-3 rounded-lg bg-cfo-accent text-black font-medium hover:bg-opacity-90 transition-colors text-sm',
            !sidebarExpanded && 'p-2'
          )}
        >
          <MessageSquare size={18} />
          {sidebarExpanded && <span>Ask AI CFO</span>}
        </button>
      </div>
    </aside>
  );
}
