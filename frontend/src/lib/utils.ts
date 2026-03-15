import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatCurrencyDetailed(value: number | null | undefined): string {
  if (value === null || value === undefined) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatMonths(months: number): string {
  if (months === null || months === undefined) return '0 months';
  if (months < 0) return 'negative';
  if (months < 1) return `${Math.round(months * 10) / 10} weeks`;
  return `${Math.round(months * 10) / 10} months`;
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '0%';
  return `${Math.round(value * 100) / 100}%`;
}

export function getRunwayColor(months: number | null | undefined): string {
  if (months === null || months === undefined) return 'bg-gray-700';
  if (months >= 12) return 'bg-green-600';
  if (months >= 6) return 'bg-yellow-600';
  if (months >= 3) return 'bg-orange-600';
  return 'bg-red-600';
}

export function getRunwayTextColor(months: number | null | undefined): string {
  if (months === null || months === undefined) return 'text-gray-400';
  if (months >= 12) return 'text-green-400';
  if (months >= 6) return 'text-yellow-400';
  if (months >= 3) return 'text-orange-400';
  return 'text-red-400';
}

export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return 'Never';
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d);
}

export function formatTime(date: string | Date | null | undefined): string {
  if (!date) return 'Never';
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(d);
}

export function daysUntilZero(months: number | null | undefined): number {
  if (months === null || months === undefined) return 0;
  return Math.round(months * 30);
}

export function formatRelativeTime(date: string | Date | null | undefined): string {
  if (!date) return 'Unknown';
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  if (diffDays < 30) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
  return formatDate(d);
}

/**
 * Simple markdown parser - returns marked ranges for rendering
 */
export function parseMarkdownRanges(text: string): Array<{
  type: 'text' | 'bold' | 'italic' | 'code';
  content: string;
}> {
  const parts: Array<{ type: 'text' | 'bold' | 'italic' | 'code'; content: string }> = [];
  let currentIndex = 0;

  // Regex for bold, italic, and code
  const regex = /\*\*(.+?)\*\*|__(.+?)__|`(.+?)`|\*(.+?)\*|_(.+?)_/g;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // Add text before match
    if (match.index > currentIndex) {
      parts.push({
        type: 'text',
        content: text.substring(currentIndex, match.index),
      });
    }

    // Add formatted match
    if (match[1]) {
      parts.push({ type: 'bold', content: match[1] });
    } else if (match[2]) {
      parts.push({ type: 'bold', content: match[2] });
    } else if (match[3]) {
      parts.push({ type: 'code', content: match[3] });
    } else if (match[4]) {
      parts.push({ type: 'italic', content: match[4] });
    } else if (match[5]) {
      parts.push({ type: 'italic', content: match[5] });
    }

    currentIndex = regex.lastIndex;
  }

  // Add remaining text
  if (currentIndex < text.length) {
    parts.push({
      type: 'text',
      content: text.substring(currentIndex),
    });
  }

  return parts.length > 0 ? parts : [{ type: 'text', content: text }];
}

/**
 * Detect scenario result in text (e.g., "Runway: 14.2 → 12.8 months")
 */
export interface ScenarioResult {
  title: string;
  metrics: Array<{ label: string; before: string; after: string }>;
}

export function extractScenarioResult(text: string): ScenarioResult | null {
  // Look for patterns like "Hiring 2 engineers" or "Adding $100k revenue"
  const titleMatch = text.match(/(Hiring|Adding|Increasing|Decreasing)\s+(.+?)(?:\n|$)/);
  if (!titleMatch) return null;

  // Look for metric patterns like "Runway: 14.2 → 12.8 months"
  const metricMatches = text.matchAll(/(.+?):\s+(\$?[\d.]+[kmb]?)\s+→\s+(\$?[\d.]+[kmb]?)/g);
  const metrics = Array.from(metricMatches).map((m) => ({
    label: m[1],
    before: m[2],
    after: m[3],
  }));

  if (metrics.length === 0) return null;

  return {
    title: titleMatch[0].trim(),
    metrics,
  };
}
