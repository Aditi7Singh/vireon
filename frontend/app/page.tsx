import Link from "next/link";

const highlights = [
  {
    title: "ERP Integration",
    subtitle: "Real-time data. Real decisions.",
    blurb: "Direct finance signals from your ERP, mapped into actionable operating metrics.",
  },
  {
    title: "What-If Simulations",
    subtitle: "Test before you commit.",
    blurb: "Model hiring, spend cuts, and growth moves against runway impact in seconds.",
  },
  {
    title: "Anomaly Detection",
    subtitle: "Spot risk before it compounds.",
    blurb: "Continuous detection for unusual spend, revenue dips, and operational outliers.",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[#eee7da] px-4 py-6 text-[#191510] sm:px-6 lg:px-10">
      <div className="mx-auto w-full max-w-6xl border-2 border-[#2f2820] bg-[#f6efe2] shadow-[0_18px_50px_rgba(51,37,24,0.25)]">
        <header className="border-b-2 border-[#2f2820] px-5 pb-5 pt-4 sm:px-8">
          <div className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-[0.14em] text-[#4b4032]">
            <span>Vol 1, No 1</span>
            <span>AI Financial Copilot for ERP Systems</span>
            <span>Price: Productive Decisions</span>
          </div>

          <h1 className="mt-4 text-center font-serif text-5xl font-bold uppercase leading-none tracking-wide text-[#1d1812] sm:text-6xl lg:text-7xl">
            Vireon Times
          </h1>

          <p className="mt-3 text-center font-serif text-3xl font-bold uppercase leading-tight text-[#201a14] sm:text-4xl">
            AI CFO Takes The Helm
          </p>
          <p className="mt-2 text-center text-base italic text-[#4d4134]">
            Transforming Financial Management for ERP-led teams.
          </p>

          <div className="mt-5 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center border-2 border-[#2f2820] bg-[#1c1712] px-8 py-3 text-sm font-bold uppercase tracking-[0.14em] text-[#f7efdf] transition-colors hover:bg-[#31281f]"
            >
              Open Vireon Dashboard
            </Link>
            <span className="text-xs uppercase tracking-[0.14em] text-[#5d4f40]">
              Click Vireon to enter your existing UI
            </span>
          </div>
        </header>

        <section className="grid gap-0 border-b-2 border-[#2f2820] md:grid-cols-3">
          {highlights.map((item, index) => (
            <article
              key={item.title}
              className={`p-5 sm:p-6 ${index < highlights.length - 1 ? "border-b-2 border-[#2f2820] md:border-b-0 md:border-r-2" : ""}`}
            >
              <h2 className="font-serif text-2xl font-bold uppercase leading-tight text-[#1d1712]">{item.title}</h2>
              <p className="mt-1 text-sm font-semibold uppercase tracking-[0.08em] text-[#6a5948]">{item.subtitle}</p>
              <p className="mt-4 text-sm leading-relaxed text-[#3f352a]">{item.blurb}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-0 border-b-2 border-[#2f2820] lg:grid-cols-[1.1fr_1fr_1fr]">
          <article className="border-b-2 border-[#2f2820] p-5 sm:p-6 lg:border-b-0 lg:border-r-2">
            <h3 className="font-serif text-3xl font-bold uppercase text-[#7d1e1e]">Anomaly Detected</h3>
            <div className="mt-4 border-2 border-[#2f2820] bg-[#efe4d1] p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#4f4336]">AI Chat Insight</p>
              <p className="mt-3 text-sm leading-relaxed text-[#2d251d]">
                &quot;Why did expenses spike last month?&quot;
              </p>
              <p className="mt-2 text-sm leading-relaxed text-[#2d251d]">
                Spend rose on marketing and cloud usage. Vireon flags the delta and recommends corrective actions.
              </p>
              <p className="mt-4 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#5d4f40]">Detailed analysis in dashboard</p>
            </div>
          </article>

          <article className="border-b-2 border-[#2f2820] p-5 sm:p-6 lg:border-b-0 lg:border-r-2">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#4f4336]">Alert: Spike in Expenses</p>
            <p className="mt-3 font-serif text-5xl font-bold text-[#9b231f]">45%</p>
            <p className="mt-1 text-sm uppercase tracking-[0.1em] text-[#5d4f40]">vs average baseline</p>

            <div className="mt-5 flex h-32 items-end gap-2 border-t border-[#9b8a73] pt-4">
              {[28, 32, 30, 36, 40, 42, 46, 44, 49, 52, 57, 35].map((bar, idx) => (
                <div key={idx} className="flex-1 bg-[#465a72]" style={{ height: `${bar * 1.8}px` }} />
              ))}
            </div>
          </article>

          <article className="p-5 sm:p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#4f4336]">Runway Forecast</p>
            <p className="mt-4 text-sm uppercase tracking-[0.08em] text-[#5d4f40]">Cash Remaining</p>
            <p className="font-serif text-5xl font-bold text-[#18130f]">$790K</p>
            <p className="mt-4 text-sm uppercase tracking-[0.08em] text-[#5d4f40]">Runway</p>
            <p className="font-serif text-5xl font-bold text-[#18130f]">5.2</p>
            <p className="mt-1 text-sm uppercase tracking-[0.08em] text-[#5d4f40]">Months</p>

            <Link
              href="/dashboard"
              className="mt-6 inline-flex border border-[#2f2820] bg-[#fff9ef] px-4 py-2 text-xs font-bold uppercase tracking-[0.12em] text-[#1f1913] transition-colors hover:bg-[#f0e4cf]"
            >
              Go to Vireon
            </Link>
          </article>
        </section>

        <footer className="grid gap-0 text-[11px] uppercase tracking-[0.1em] text-[#4d4134] md:grid-cols-4">
          {[
            "Loan & Depreciation Calculations",
            "Multi-Currency Support in Progress",
            "PDF Reports Available",
            "Cloud Deployment with AWS + Ollama",
          ].map((line, index) => (
            <div
              key={line}
              className={`px-4 py-3 ${index < 3 ? "border-b border-[#2f2820] md:border-b-0 md:border-r" : ""}`}
            >
              {line}
            </div>
          ))}
        </footer>
      </div>
    </main>
  );
}
