import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  showText?: boolean;
  variant?: "gradient" | "white" | "dark";
}

const sizes = {
  xs: { icon: "w-6 h-6", text: "text-base", p: "p-1" },
  sm: { icon: "w-8 h-8", text: "text-xl", p: "p-1.5" },
  md: { icon: "w-10 h-10", text: "text-2xl", p: "p-2" },
  lg: { icon: "w-12 h-12", text: "text-3xl", p: "p-2.5" },
  xl: { icon: "w-16 h-16", text: "text-4xl", p: "p-3" },
};

export function Logo({ className, size = "md", showText = true, variant = "gradient" }: LogoProps) {
  const sizeClasses = sizes[size];

  return (
    <div className={cn("flex items-center gap-3 transition-all duration-300 group/logo", className)}>
      {/* Icon */}
      <div className={cn(
        "relative flex items-center justify-center rounded-xl transition-transform duration-500 group-hover/logo:scale-110",
        sizeClasses.icon,
        variant === "gradient" && "bg-gradient-to-tr from-[#c46f34] to-[#7a4828] shadow-lg shadow-[#7a4828]/25",
        variant === "white" && "bg-white/10 backdrop-blur-sm border border-white/20",
        variant === "dark" && "bg-slate-900 border border-slate-800"
      )}>
        <svg
          viewBox="0 0 40 40"
          className={cn("text-white", sizeClasses.p === "p-1" ? "w-4 h-4" : sizeClasses.p === "p-1.5" ? "w-5 h-5" : "w-6 h-6")}
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <path
            d="M6 24C12 16 21 12 33 11L24 19H34L20 32L24 24H14Z"
            fill="currentColor"
            opacity="0.95"
          />
          <path
            d="M8 28C13 22 18 19 24 18"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            opacity="0.55"
          />
        </svg>

        {/* Subtle shine effect */}
        {variant === "gradient" && (
          <div className="absolute inset-0 rounded-xl bg-gradient-to-tr from-white/20 via-transparent to-transparent pointer-events-none" />
        )}
      </div>

      {/* Text */}
      {showText && (
        <div className="flex flex-col leading-none">
          <span className={cn(
            "font-black tracking-[-0.04em] font-outfit uppercase",
            sizeClasses.text,
            variant === "gradient" ? "text-slate-900 dark:text-white" : "text-white"
          )}>
            Vireon
          </span>
          <span className={cn(
            "mt-1.5 text-[11px] font-bold tracking-[0.08em] hidden sm:block",
            variant === "gradient" ? "text-slate-500" : "text-[#f3c7a9]"
          )}>
            Always watching your runway
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
