'use client';

import { useState } from 'react';
import { Runway } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Zap, Settings2 } from 'lucide-react';
import { ScenarioModal } from '@/components/scenarios/ScenarioModal';

interface Props {
  data: Runway | null;
  loading: boolean;
}

export function RunwayCard({ data, loading }: Props) {
  const [scenarioOpen, setScenarioOpen] = useState(false);

  if (loading) {
    return (
      <div className="col-span-2 lg:col-span-1 p-8 rounded-lg bg-cfo-surface border border-cfo-border animate-pulse">
        <div className="h-32 bg-cfo-surface2 rounded" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="col-span-2 lg:col-span-1 p-8 rounded-lg bg-cfo-surface border border-cfo-border text-center">
        <p className="text-cfo-muted">Unable to load runway data</p>
      </div>
    );
  }

  const months = data.runway_months;

  // Determine color based on severity
  let bgColor = 'bg-green-500/10';
  let borderColor = 'border-green-500/30';
  let textColor = 'text-green-400';
  let labelColor = 'text-green-300';
  let shouldPulse = false;

  if (months >= 12) {
    // Green - healthy
    bgColor = 'bg-green-500/10';
    borderColor = 'border-green-500/30';
    textColor = 'text-green-400';
    labelColor = 'text-green-300';
  } else if (months >= 9) {
    // Yellow - warning
    bgColor = 'bg-yellow-500/10';
    borderColor = 'border-yellow-500/30';
    textColor = 'text-yellow-400';
    labelColor = 'text-yellow-300';
  } else if (months >= 6) {
    // Orange - caution
    bgColor = 'bg-orange-500/10';
    borderColor = 'border-orange-500/30';
    textColor = 'text-orange-400';
    labelColor = 'text-orange-300';
  } else {
    // Red - critical with pulsing
    bgColor = 'bg-red-500/10';
    borderColor = 'border-red-500/30';
    textColor = 'text-red-400';
    labelColor = 'text-red-300';
    shouldPulse = true;
  }

  const zeroDate = new Date(data.zero_date);
  const confidenceWeeks = data.confidence_interval?.high || 1;

  return (
    <div
      className={cn(
        'col-span-2 lg:col-span-1 p-8 rounded-lg border transition-all duration-300',
        bgColor,
        borderColor,
        shouldPulse && 'animate-pulse ring-2 ring-red-500/20'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-sm font-semibold text-cfo-muted uppercase tracking-wider">
          Cash Runway
        </h2>
        <div className="flex items-center gap-2">
          <Zap className={cn('w-5 h-5', shouldPulse ? 'animate-spin' : '')} />
          <button
            onClick={() => setScenarioOpen(true)}
            className="p-1.5 rounded hover:bg-white/10 transition"
            title="Open scenario simulator"
          >
            <Settings2 className="w-4 h-4 text-cfo-muted hover:text-white" />
          </button>
        </div>
      </div>

      {/* Hero Number */}
      <div className={cn('mb-6', textColor)}>
        <div className="text-6xl font-black leading-none mb-2">
          {months.toFixed(1)}
        </div>
        <div className={cn('text-lg font-medium', labelColor)}>
          months remaining
        </div>
      </div>

      {/* Confidence Interval */}
      <div className={cn('text-xs mb-5 pb-5 border-b', borderColor, 'text-cfo-muted')}>
        Confidence: ±{confidenceWeeks} weeks
      </div>

      {/* Zero Date */}
      <div>
        <p className="text-xs text-cfo-muted mb-1">Zero date</p>
        <p className={cn('text-sm font-medium', textColor)}>
          {zeroDate.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric',
          })}
        </p>
      </div>

      {/* Scenario Modal */}
      <ScenarioModal
        open={scenarioOpen}
        onOpenChange={setScenarioOpen}
        currentRunway={months}
        currentBurn={data.monthly_burn}
        currentMrr={100000}
      />
    </div>
  );
}
