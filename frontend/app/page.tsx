"use client";

import Link from "next/link";
import { ArrowRight, Cpu, ShieldCheck, Sparkles, TrendingUp } from "lucide-react";
import { Logo } from "@/components/Logo";

const pillars = [
  {
    title: "Deterministic Finance Core",
    description: "Metric computation stays auditable and math-backed, even when questions are asked in natural language.",
    icon: Cpu,
  },
  {
    title: "Early Risk Detection",
    description: "Anomaly scans surface unusual spend patterns before they materially affect runway and operating tempo.",
    icon: ShieldCheck,
  },
  {
    title: "Strategic Scenario Layer",
    description: "Model hiring, cloud cost, and growth choices with concrete INR impact and timeline sensitivity.",
    icon: TrendingUp,
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-[#f6f3ee] text-[#1d1b19] overflow-hidden">
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute -top-32 -left-24 h-[28rem] w-[28rem] rounded-full bg-[#f8caa8]/35 blur-3xl" />
        <div className="absolute top-[18%] right-[-10rem] h-[30rem] w-[30rem] rounded-full bg-[#f0d9bc]/45 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_10%,rgba(255,255,255,0.8),transparent_42%),radial-gradient(circle_at_90%_20%,rgba(254,245,236,0.95),transparent_40%)]" />
      </div>

      <header className="relative z-20 mx-auto flex w-full max-w-[1280px] items-center justify-between px-6 py-8 lg:px-12">
        <Logo size="sm" />

        <nav className="hidden items-center gap-10 md:flex">
          {[
            { label: "Platform", href: "#platform" },
            { label: "Intelligence", href: "#capabilities" },
            { label: "Security", href: "#security" },
            { label: "Pricing", href: "#pricing" },
          ].map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className="text-sm text-[#4d463f] transition-colors hover:text-[#1f1a16]"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <Link
          href="/dashboard"
          className="rounded-full border border-[#d7c9b9] bg-white/70 px-5 py-2.5 text-sm font-medium text-[#201c18] shadow-sm transition-all hover:border-[#c7b3a0] hover:bg-white"
        >
          Open Dashboard
        </Link>
      </header>

      <main className="relative z-10 mx-auto flex w-full max-w-[1280px] flex-col px-6 pb-20 pt-6 lg:px-12 lg:pt-10">
        <section id="platform" className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-[#d9cbbd] bg-white/70 px-4 py-1.5 text-xs font-medium uppercase tracking-[0.16em] text-[#735d48]">
              <Sparkles className="h-3.5 w-3.5" />
              AI CFO for operational teams
            </div>

            <h1 className="mt-7 max-w-3xl text-5xl font-semibold leading-[0.96] tracking-tight text-[#1d1b19] md:text-7xl">
              Financial clarity that feels
              <span className="bg-gradient-to-r from-[#cc6d2b] via-[#a95a29] to-[#6f3f1f] bg-clip-text text-transparent"> immediate</span>.
            </h1>

            <p className="mt-7 max-w-2xl text-base leading-relaxed text-[#5a5148] md:text-lg">
              Vireon turns ERP complexity into plain-language financial decisions.
              From burn diagnostics to runway projections, every insight is traceable,
              explainable, and ready for leadership action.
            </p>

            <p className="mt-4 text-sm font-semibold uppercase tracking-[0.14em] text-[#8a603e]">
              Always watching your runway.
            </p>

            <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center">
              <Link
                href="/dashboard"
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-[#1f1a16] px-7 py-4 text-sm font-medium text-[#fff6ee] shadow-[0_14px_40px_rgba(34,20,10,0.22)] transition-all hover:translate-y-[-1px] hover:bg-[#151210]"
              >
                Launch Vireon
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="#capabilities"
                className="inline-flex items-center justify-center rounded-2xl border border-[#d3c3b2] bg-white/65 px-7 py-4 text-sm font-medium text-[#2c2722] transition-colors hover:bg-white"
              >
                Explore capabilities
              </Link>
            </div>
          </div>

          <div className="rounded-[2rem] border border-[#dbcfc1] bg-[linear-gradient(160deg,#fffdf9_0%,#f7eee3_100%)] p-7 shadow-[0_20px_60px_rgba(70,42,18,0.12)]">
            <p className="text-xs font-medium uppercase tracking-[0.15em] text-[#7a664f]">Live Snapshot</p>
            <div className="mt-4 space-y-4">
              {[
                ["Current runway", "9.4 months"],
                ["Net burn", "INR 12.4L / month"],
                ["Burn multiple", "1.8x"],
              ].map(([label, value]) => (
                <div key={label} className="flex items-center justify-between rounded-xl border border-[#eadfce] bg-white/80 px-4 py-3">
                  <span className="text-sm text-[#6f655a]">{label}</span>
                  <span className="text-sm font-semibold text-[#221f1b]">{value}</span>
                </div>
              ))}
            </div>
            <p className="mt-6 text-xs leading-relaxed text-[#6f655a]">
              Unified view across ERP, payroll, cloud spend, and manual team inputs.
              Built for founders, finance leads, and operating partners.
            </p>
          </div>
        </section>

        <section id="capabilities" className="mt-24 grid gap-5 md:grid-cols-3">
          {pillars.map((item) => (
            <article
              key={item.title}
              className="rounded-[1.6rem] border border-[#ddd1c3] bg-white/70 p-6 shadow-[0_10px_35px_rgba(72,44,23,0.08)] backdrop-blur"
            >
              <div className="mb-5 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-[#f8eee3] text-[#8c4d24]">
                <item.icon className="h-5 w-5" />
              </div>
              <h3 className="text-xl font-semibold tracking-tight text-[#201c18]">{item.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-[#5e554b]">{item.description}</p>
            </article>
          ))}
        </section>

        <section id="security" className="mt-10 rounded-[1.8rem] border border-[#d9ccbc] bg-white/65 p-8 shadow-[0_10px_30px_rgba(70,42,18,0.06)]">
          <h2 className="text-2xl font-semibold tracking-tight text-[#201c18]">Security by default</h2>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-[#5e554b]">
            Role-aware access, deterministic calculation paths, and auditable financial outputs are built into the platform baseline.
            Designed for teams that need speed without sacrificing trust.
          </p>
        </section>

        <section id="pricing" className="mt-6 rounded-[1.8rem] border border-[#d9ccbc] bg-[linear-gradient(160deg,#fffdf8_0%,#f5ebde_100%)] p-8 shadow-[0_14px_34px_rgba(70,42,18,0.08)]">
          <h2 className="text-2xl font-semibold tracking-tight text-[#201c18]">Built for operator-led teams</h2>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-[#5e554b]">
            Start with core runway intelligence and scale into deep planning, anomaly operations, and role-specific finance workflows.
          </p>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <Link href="/dashboard" className="inline-flex items-center justify-center rounded-xl bg-[#1f1a16] px-5 py-3 text-sm font-medium text-[#fff6ee]">
              Start Product Tour
            </Link>
            <Link href="#" className="inline-flex items-center justify-center rounded-xl border border-[#cebda8] bg-white/70 px-5 py-3 text-sm font-medium text-[#2c2722]">
              Request Demo Access
            </Link>
          </div>
        </section>
      </main>

      <footer className="relative z-10 border-t border-[#dccfbe] bg-white/55">
        <div className="mx-auto flex w-full max-w-[1280px] flex-col items-center justify-between gap-4 px-6 py-7 text-sm text-[#665d54] md:flex-row lg:px-12">
          <span>© 2026 SeedlingLabs. Built with financial discipline.</span>
          <div className="flex items-center gap-6">
            <Link href="#" className="hover:text-[#2a241f]">Privacy</Link>
            <Link href="#" className="hover:text-[#2a241f]">Security</Link>
            <Link href="#" className="hover:text-[#2a241f]">Status</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
