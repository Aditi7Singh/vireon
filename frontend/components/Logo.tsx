"use client";

import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  showText?: boolean;
  variant?: "gradient" | "white" | "dark";
}

const sizes = {
  xs: { icon: "w-6 h-6", text: "text-sm", p: "p-1" },
  sm: { icon: "w-8 h-8", text: "text-lg", p: "p-1.5" },
  md: { icon: "w-10 h-10", text: "text-xl", p: "p-2" },
  lg: { icon: "w-12 h-12", text: "text-2xl", p: "p-2.5" },
  xl: { icon: "w-16 h-16", text: "text-3xl", p: "p-3" },
};

export function Logo({ className, size = "md", showText = true, variant = "gradient" }: LogoProps) {
  const sizeClasses = sizes[size];

  return (
    <div className={cn("flex items-center gap-3 transition-all duration-300", className)}>
      {/* Icon */}
      <div className={cn(
        "relative flex items-center justify-center rounded-xl",
        sizeClasses.icon,
        variant === "gradient" && "bg-gradient-to-br from-indigo-500 via-purple-500 to-indigo-600 shadow-lg shadow-indigo-500/20",
        variant === "white" && "bg-white/10 backdrop-blur-sm border border-white/20",
        variant === "dark" && "bg-slate-900 border border-slate-800"
      )}>
        {/* V Letter with subtle animation */}
        <svg
          viewBox="0 0 24 24"
          fill="none"
          className={cn("w-full h-full", sizeClasses.p)}
        >
          <defs>
            <linearGradient id="vireonGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="currentColor" stopOpacity="1" />
              <stop offset="100%" stopColor="currentColor" stopOpacity="0.8" />
            </linearGradient>
          </defs>
          <path
            d="M4 6L12 20L20 6"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn(
              variant === "gradient" ? "text-white" : "text-white"
            )}
          />
          {/* Inner accent line */}
          <path
            d="M7 8L12 18L17 8"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn(
              "opacity-40",
              variant === "gradient" ? "text-white" : "text-white"
            )}
          />
        </svg>
        
        {/* Subtle shine effect */}
        {variant === "gradient" && (
          <div className="absolute inset-0 rounded-xl bg-gradient-to-tr from-white/20 via-transparent to-transparent pointer-events-none" />
        )}
      </div>

      {/* Text */}
      {showText && (
        <div className="flex flex-col">
          <span className={cn(
            "font-bold tracking-tight font-outfit leading-none",
            sizeClasses.text,
            variant === "gradient" ? "text-slate-900 dark:text-white" : "text-white"
          )}>
            Vireon
          </span>
          <span className={cn(
            "text-[10px] font-medium uppercase tracking-wider mt-1 hidden sm:block",
            variant === "gradient" ? "text-slate-500" : "text-slate-400"
          )}>
            AI CFO
          </span>
        </div>
      )}
    </div>
  );
}

export function LogoIcon({ className, variant = "gradient" }: { className?: string, variant?: "gradient" | "white" | "dark" }) {
  return <Logo showText={false} variant={variant} className={className} size="md" />;
}

export default Logo;
