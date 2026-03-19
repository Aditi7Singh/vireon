import { cn } from "@/lib/utils";
import { Hexagon } from "lucide-react";

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
    <div className={cn("flex items-center gap-3 transition-all duration-300 group/logo", className)}>
      {/* Icon */}
      <div className={cn(
        "relative flex items-center justify-center rounded-xl transition-transform duration-500 group-hover/logo:scale-110",
        sizeClasses.icon,
        variant === "gradient" && "bg-gradient-to-tr from-indigo-600 to-purple-600 shadow-lg shadow-indigo-600/20",
        variant === "white" && "bg-white/10 backdrop-blur-sm border border-white/20",
        variant === "dark" && "bg-slate-900 border border-slate-800"
      )}>
        <Hexagon className={cn("text-white", sizeClasses.p === "p-1" ? "w-4 h-4" : sizeClasses.p === "p-1.5" ? "w-5 h-5" : "w-6 h-6")} />

        {/* Subtle shine effect */}
        {variant === "gradient" && (
          <div className="absolute inset-0 rounded-xl bg-gradient-to-tr from-white/20 via-transparent to-transparent pointer-events-none" />
        )}
      </div>

      {/* Text */}
      {showText && (
        <div className="flex flex-col">
          <span className={cn(
            "font-black tracking-tighter font-outfit leading-none uppercase",
            sizeClasses.text,
            variant === "gradient" ? "text-slate-900 dark:text-white" : "text-white"
          )}>
            Vireon
          </span>
          <span className={cn(
            "text-[9px] font-black uppercase tracking-[0.2em] mt-1 hidden sm:block",
            variant === "gradient" ? "text-slate-500" : "text-indigo-400"
          )}>
            by SeedlingLabs
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
