'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { AlertCircle, AlertTriangle, Send, X } from 'lucide-react';
import { formatCurrency, cn } from '@/lib/utils';
import { useAppStore } from '@/lib/store';

interface ScenarioResult {
  currentRunway: number;
  newRunway: number;
  runwayDelta: number;
  monthlyBurnDelta: number;
  breakEvenMrr?: number;
  zeroDate?: string;
  monthlySavings?: number;
}

interface ScenarioModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentRunway: number;
  currentBurn: number;
  currentMrr: number;
}

export function ScenarioModal({
  open,
  onOpenChange,
  currentRunway,
  currentBurn,
  currentMrr,
}: ScenarioModalProps) {
  const [activeTab, setActiveTab] = useState('hire');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScenarioResult | null>(null);

  // Hire Engineers tab state
  const [engineerCount, setEngineerCount] = useState(1);
  const [avgSalary, setAvgSalary] = useState(120000);

  // Revenue Change tab state
  const [mrrDelta, setMrrDelta] = useState(50000);
  const [probability, setProbability] = useState(100);

  // Cut Expenses tab state
  const [expenseCategory, setExpenseCategory] = useState('all');
  const [reductionPercent, setReductionPercent] = useState(10);

  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const openChat = useAppStore((state) => state.openChat);

  // API call for hire engineers scenario
  const callHireScenario = useCallback(async (engineers: number, salary: number) => {
    setLoading(true);
    try {
      const response = await fetch('/api/scenario/hire', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          numEngineers: engineers,
          avgSalary: salary,
          currentRunway,
          currentBurn,
          currentMrr,
        }),
      });
      if (!response.ok) throw new Error('Failed to calculate scenario');
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Scenario error:', error);
    } finally {
      setLoading(false);
    }
  }, [currentRunway, currentBurn, currentMrr]);

  // API call for revenue change scenario
  const callRevenueScenario = useCallback(async (delta: number, prob: number) => {
    setLoading(true);
    try {
      const response = await fetch('/api/scenario/revenue-change', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mrrDelta: delta,
          probability: prob,
          currentRunway,
          currentBurn,
          currentMrr,
        }),
      });
      if (!response.ok) throw new Error('Failed to calculate scenario');
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Scenario error:', error);
    } finally {
      setLoading(false);
    }
  }, [currentRunway, currentBurn, currentMrr]);

  // API call for cut expenses scenario
  const callCutExpenseScenario = useCallback(async (category: string, percent: number) => {
    setLoading(true);
    try {
      const response = await fetch('/api/scenario/cut-expenses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category,
          reductionPercent: percent,
          currentRunway,
          currentBurn,
          currentMrr,
        }),
      });
      if (!response.ok) throw new Error('Failed to calculate scenario');
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Scenario error:', error);
    } finally {
      setLoading(false);
    }
  }, [currentRunway, currentBurn, currentMrr]);

  // Debounced handlers for slider changes
  const handleEngineerChange = (count: number) => {
    setEngineerCount(count);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      callHireScenario(count, avgSalary);
    }, 300);
  };

  const handleSalaryChange = (salary: number) => {
    setAvgSalary(salary);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      callHireScenario(engineerCount, salary);
    }, 300);
  };

  const handleMrrDeltaChange = (delta: number) => {
    setMrrDelta(delta);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      callRevenueScenario(delta, probability);
    }, 300);
  };

  const handleProbabilityChange = (prob: number) => {
    setProbability(prob);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      callRevenueScenario(mrrDelta, prob);
    }, 300);
  };

  const handleReductionChange = (percent: number) => {
    setReductionPercent(percent);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      callCutExpenseScenario(expenseCategory, percent);
    }, 300);
  };

  const handleCategoryChange = (category: string) => {
    setExpenseCategory(category);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      callCutExpenseScenario(category, reductionPercent);
    }, 300);
  };

  // Initial load when modal opens
  useEffect(() => {
    if (open && !result) {
      callHireScenario(engineerCount, avgSalary);
    }
  }, [open]);

  const handleAskAI = () => {
    const scenarioText = generateScenarioSummary();
    openChat();
    // The chat drawer will be opened and can receive the scenario text via props or store
  };

  const generateScenarioSummary = (): string => {
    if (!result) return '';

    let summary = '';
    if (activeTab === 'hire') {
      summary = `I'm considering hiring ${engineerCount} engineer(s) at ${formatCurrency(avgSalary)}/year. Current runway: ${currentRunway.toFixed(1)} months. New runway would be ${result.newRunway.toFixed(1)} months (${result.runwayDelta > 0 ? '+' : ''}${result.runwayDelta.toFixed(1)} months). Monthly burn would increase by ${formatCurrency(result.monthlyBurnDelta)}. What are your thoughts?`;
    } else if (activeTab === 'revenue') {
      summary = `I'm modeling a ${mrrDelta > 0 ? '+' : ''}${formatCurrency(mrrDelta)} MRR change with ${probability}% probability. This would change runway from ${currentRunway.toFixed(1)} to ${result.newRunway.toFixed(1)} months. What's your recommendation?`;
    } else if (activeTab === 'expenses') {
      summary = `I'm considering a ${reductionPercent}% cost cut in ${expenseCategory}. This would save ${formatCurrency(result.monthlySavings || 0)}/month and extend runway to ${result.newRunway.toFixed(1)} months. Should I proceed?`;
    }
    return summary;
  };

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => onOpenChange(false)}
          aria-label="Close modal"
        />
      )}

      {/* Modal */}
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="bg-cfo-surface border border-cfo-border rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            {/* Header */}
            <div className="sticky top-0 bg-cfo-surface border-b border-cfo-border px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-white">Financial Scenarios</h2>
                <p className="text-sm text-cfo-muted mt-1">
                  Run &quot;what if&quot; calculations to see how decisions impact your runway
                </p>
              </div>
              <button
                onClick={() => onOpenChange(false)}
                className="text-cfo-muted hover:text-white transition"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Warning banners */}
              {result && (
                <div className="space-y-2">
                  {result.runwayDelta < -2 && (
                    <div className="flex items-center gap-2 px-4 py-3 bg-amber-900/20 border border-amber-700 rounded">
                      <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0" />
                      <span className="text-sm text-amber-200">
                        Runway decreases by {Math.abs(result.runwayDelta).toFixed(1)} months
                      </span>
                    </div>
                  )}
                  {result.newRunway < 6 && (
                    <div className="flex items-center gap-2 px-4 py-3 bg-red-900/20 border border-red-700 rounded">
                      <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                      <span className="text-sm text-red-200">
                        ⚠️ Critical: New runway is only {result.newRunway.toFixed(1)} months
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Tabs */}
              <div className="border-b border-cfo-border">
                <div className="flex gap-1">
                  {['hire', 'revenue', 'expenses'].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={cn(
                        'px-4 py-3 text-sm font-medium border-b-2 transition -mb-px',
                        activeTab === tab
                          ? 'border-cfo-accent text-white'
                          : 'border-transparent text-cfo-muted hover:text-white'
                      )}
                    >
                      {tab === 'hire' && 'Hire Engineers'}
                      {tab === 'revenue' && 'Revenue Change'}
                      {tab === 'expenses' && 'Cut Expenses'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tab Content */}
              <div className="space-y-6">
                {/* TAB 1: Hire Engineers */}
                {activeTab === 'hire' && (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-cfo-muted mb-2">
                        Number of Engineers: <span className="text-white font-semibold">{engineerCount}</span>
                      </label>
                      <input
                        type="range"
                        min="1"
                        max="10"
                        value={engineerCount}
                        onChange={(e) => handleEngineerChange(parseInt(e.target.value))}
                        className="w-full h-2 bg-cfo-surface2 rounded-lg appearance-none cursor-pointer accent-cfo-accent"
                      />
                      <div className="flex justify-between text-xs text-cfo-muted mt-1">
                        <span>1</span>
                        <span>10</span>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-cfo-muted mb-2">
                        Average Salary: <span className="text-white font-semibold">{formatCurrency(avgSalary)}</span>
                      </label>
                      <input
                        type="range"
                        min="80000"
                        max="200000"
                        step="5000"
                        value={avgSalary}
                        onChange={(e) => handleSalaryChange(parseInt(e.target.value))}
                        className="w-full h-2 bg-cfo-surface2 rounded-lg appearance-none cursor-pointer accent-cfo-accent"
                      />
                      <div className="flex justify-between text-xs text-cfo-muted mt-1">
                        <span>$80k</span>
                        <span>$200k</span>
                      </div>
                    </div>

                    <div className="p-4 bg-cfo-surface2 rounded-lg border border-cfo-border">
                      <p className="text-sm text-cfo-muted mb-2">Monthly Impact:</p>
                      <p className="text-lg font-semibold text-white">
                        +{formatCurrency((engineerCount * avgSalary) / 12)}
                      </p>
                    </div>
                  </div>
                )}

                {/* TAB 2: Revenue Change */}
                {activeTab === 'revenue' && (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-cfo-muted mb-2">
                        MRR Delta: <span className="text-white font-semibold">{mrrDelta > 0 ? '+' : ''}{formatCurrency(mrrDelta)}</span>
                      </label>
                      <input
                        type="range"
                        min="-100000"
                        max="100000"
                        step="5000"
                        value={mrrDelta}
                        onChange={(e) => handleMrrDeltaChange(parseInt(e.target.value))}
                        className="w-full h-2 bg-cfo-surface2 rounded-lg appearance-none cursor-pointer accent-cfo-accent"
                      />
                      <div className="flex justify-between text-xs text-cfo-muted mt-1">
                        <span>-$100k</span>
                        <span>+$100k</span>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-cfo-muted mb-2">
                        Probability: <span className="text-white font-semibold">{probability}%</span>
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={probability}
                        onChange={(e) => handleProbabilityChange(parseInt(e.target.value))}
                        className="w-full h-2 bg-cfo-surface2 rounded-lg appearance-none cursor-pointer accent-cfo-accent"
                      />
                      <div className="flex justify-between text-xs text-cfo-muted mt-1">
                        <span>0%</span>
                        <span>100%</span>
                      </div>
                    </div>

                    <div className="p-4 bg-cfo-surface2 rounded-lg border border-cfo-border">
                      <p className="text-sm text-cfo-muted mb-2">Expected Monthly Change:</p>
                      <p className={cn('text-lg font-semibold', mrrDelta > 0 ? 'text-green-400' : 'text-red-400')}>
                        {mrrDelta > 0 ? '+' : ''}{formatCurrency((mrrDelta * probability) / 100)}
                      </p>
                    </div>
                  </div>
                )}

                {/* TAB 3: Cut Expenses */}
                {activeTab === 'expenses' && (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-cfo-muted mb-2">
                        Expense Category: <span className="text-white font-semibold capitalize">{expenseCategory}</span>
                      </label>
                      <select
                        value={expenseCategory}
                        onChange={(e) => handleCategoryChange(e.target.value)}
                        className="w-full px-3 py-2 bg-cfo-surface2 border border-cfo-border rounded text-white text-sm focus:outline-none focus:border-cfo-accent"
                      >
                        <option value="all">All Expenses</option>
                        <option value="aws">AWS & Infrastructure</option>
                        <option value="payroll">Payroll</option>
                        <option value="saas">SaaS Tools</option>
                        <option value="marketing">Marketing</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-cfo-muted mb-2">
                        Reduction: <span className="text-white font-semibold">{reductionPercent}%</span>
                      </label>
                      <input
                        type="range"
                        min="5"
                        max="50"
                        value={reductionPercent}
                        onChange={(e) => handleReductionChange(parseInt(e.target.value))}
                        className="w-full h-2 bg-cfo-surface2 rounded-lg appearance-none cursor-pointer accent-cfo-accent"
                      />
                      <div className="flex justify-between text-xs text-cfo-muted mt-1">
                        <span>5%</span>
                        <span>50%</span>
                      </div>
                    </div>

                    {result?.monthlySavings && (
                      <div className="p-4 bg-cfo-surface2 rounded-lg border border-cfo-border">
                        <p className="text-sm text-cfo-muted mb-2">Monthly Savings:</p>
                        <p className="text-lg font-semibold text-green-400">
                          {formatCurrency(result.monthlySavings)}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Result Display */}
              {loading ? (
                <div className="space-y-3 p-4 bg-cfo-surface2 rounded-lg border border-cfo-border">
                  <div className="h-5 bg-cfo-border rounded animate-pulse" />
                  <div className="h-5 w-3/4 bg-cfo-border rounded animate-pulse" />
                  <div className="h-5 w-1/2 bg-cfo-border rounded animate-pulse" />
                </div>
              ) : result ? (
                <div className="p-4 bg-cfo-surface2 rounded-lg border border-cfo-border space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-cfo-muted">Current Runway</p>
                      <p className="text-lg font-semibold text-white">{currentRunway.toFixed(1)} months</p>
                    </div>
                    <div>
                      <p className="text-xs text-cfo-muted">New Runway</p>
                      <p className={cn('text-lg font-semibold', result.runwayDelta > 0 ? 'text-green-400' : 'text-red-400')}>
                        {result.newRunway.toFixed(1)} months
                      </p>
                    </div>
                  </div>

                  {result.runwayDelta !== 0 && (
                    <div className="border-t border-cfo-border pt-3">
                      <p className="text-xs text-cfo-muted mb-2">Runway Change</p>
                      <p className={cn('text-lg font-semibold', result.runwayDelta > 0 ? 'text-green-400' : 'text-red-400')}>
                        {result.runwayDelta > 0 ? '+' : ''}{result.runwayDelta.toFixed(1)} months
                      </p>
                    </div>
                  )}

                  {result.monthlyBurnDelta !== 0 && (
                    <div className="border-t border-cfo-border pt-3">
                      <p className="text-xs text-cfo-muted mb-2">Monthly Burn Change</p>
                      <p className={cn('text-lg font-semibold', result.monthlyBurnDelta > 0 ? 'text-red-400' : 'text-green-400')}>
                        {result.monthlyBurnDelta > 0 ? '+' : ''}{formatCurrency(result.monthlyBurnDelta)}
                      </p>
                    </div>
                  )}

                  {result.breakEvenMrr && (
                    <div className="border-t border-cfo-border pt-3">
                      <p className="text-xs text-cfo-muted mb-2">Break-even MRR Needed</p>
                      <p className="text-lg font-semibold text-cfo-accent">+{formatCurrency(result.breakEvenMrr)}</p>
                    </div>
                  )}

                  {result.zeroDate && (
                    <div className="border-t border-cfo-border pt-3">
                      <p className="text-xs text-cfo-muted mb-2">Zero Date</p>
                      <p className="text-lg font-semibold text-white">{result.zeroDate}</p>
                    </div>
                  )}
                </div>
              ) : null}
            </div>

            {/* Footer Actions */}
            <div className="sticky bottom-0 bg-cfo-surface border-t border-cfo-border px-6 py-4 flex gap-3 justify-end">
              <button
                onClick={() => onOpenChange(false)}
                className="px-4 py-2 rounded border border-cfo-border text-white hover:bg-cfo-surface2 transition"
              >
                Close
              </button>
              <button
                onClick={handleAskAI}
                disabled={!result}
                className={cn(
                  'px-4 py-2 rounded font-semibold flex items-center gap-2 transition',
                  result
                    ? 'bg-cfo-accent hover:bg-cfo-accent/90 text-black'
                    : 'bg-cfo-muted text-cfo-surface cursor-not-allowed'
                )}
              >
                <Send className="w-4 h-4" />
                Ask AI
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
