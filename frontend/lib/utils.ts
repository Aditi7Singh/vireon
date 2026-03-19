import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency: string = "USD"): string {
  const numeric = Number(amount);
  if (!Number.isFinite(numeric)) {
    return "-";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(numeric);
}

export function formatNumber(num: number): string {
  const numeric = Number(num);
  if (!Number.isFinite(numeric)) {
    return "-";
  }

  return new Intl.NumberFormat("en-US").format(numeric);
}

export function formatCompactNumber(num?: number | null): string {
  if (num == null || Number.isNaN(num)) {
    return "-";
  }

  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

export function formatPercentage(num: number, decimals: number = 1): string {
  const numeric = Number(num);
  if (!Number.isFinite(numeric)) {
    return "-";
  }
  return `${numeric.toFixed(decimals)}%`;
}

export function formatDate(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatRelativeTime(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return "Just now";
}

export function getRunwayStatus(runwayMonths: number): {
  label: string;
  color: string;
  bgColor: string;
} {
  if (runwayMonths >= 18) {
    return { label: "Healthy", color: "text-emerald-600", bgColor: "bg-emerald-50" };
  }
  if (runwayMonths >= 12) {
    return { label: "Good", color: "text-green-600", bgColor: "bg-green-50" };
  }
  if (runwayMonths >= 9) {
    return { label: "Warning", color: "text-amber-600", bgColor: "bg-amber-50" };
  }
  if (runwayMonths >= 6) {
    return { label: "Caution", color: "text-orange-600", bgColor: "bg-orange-50" };
  }
  return { label: "Critical", color: "text-red-600", bgColor: "bg-red-50" };
}
