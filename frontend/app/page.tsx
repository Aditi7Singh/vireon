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

const frontPageStories = [
  {
    kicker: "ERP Integration",
    title: "Real-Time Data, Real Results",
    blurb: "Direct finance signals from your ERP, mapped into actionable operating metrics.",
  },
  {
    kicker: "What-If Simulations",
    title: "Test Before You Commit",
    blurb: "Model hiring, spend cuts, and growth moves against runway impact in seconds.",
  },
  {
    kicker: "Anomaly Detection",
    title: "Spot Risk Before It Compounds",
    blurb: "Continuous detection for unusual spend, revenue dips, and operational outliers.",
  },
];

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-[#e8dfcf] px-4 py-6 text-[#191510] sm:px-6 lg:px-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.7),transparent_32%),radial-gradient(circle_at_top_right,rgba(187,143,86,0.16),transparent_28%),linear-gradient(180deg,#eee4d2_0%,#e5d7c0_100%)]" />
      <div className="absolute inset-0 opacity-[0.18] [background-image:repeating-linear-gradient(0deg,rgba(37,30,22,0.09)_0px,rgba(37,30,22,0.09)_1px,transparent_1px,transparent_8px),repeating-linear-gradient(90deg,rgba(37,30,22,0.045)_0px,rgba(37,30,22,0.045)_1px,transparent_1px,transparent_12px)]" />
      <div className="absolute left-6 top-8 h-40 w-40 rounded-full bg-[#af8c5f]/20 blur-3xl" />
      <div className="absolute right-0 top-1/3 h-64 w-64 rounded-full bg-[#6a7f92]/10 blur-3xl" />

      <div className="relative mx-auto w-full max-w-6xl border-[3px] border-[#2f2820] bg-[#f5ede0] shadow-[0_18px_50px_rgba(51,37,24,0.25)]">
        <header className="border-b-2 border-[#2f2820] px-5 pb-5 pt-4 sm:px-8">
          <div className="flex items-center justify-between gap-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-[#4b4032]">
            <span>Vol 12, No. 3</span>
            <span className="text-center">AI Financial Copilot for ERP Systems</span>
            <span>Always Watching Your Runway</span>
          </div>

          <h1 className="mt-4 text-center font-serif text-5xl font-bold uppercase leading-none tracking-[0.06em] text-[#1d1812] sm:text-6xl lg:text-7xl">
            Vireon Times
          </h1>

          <div className="mx-auto mt-5 grid max-w-5xl gap-5 border-y-2 border-[#2f2820] py-5 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="space-y-4 text-center lg:text-left">
              <p className="font-serif text-3xl font-bold uppercase leading-tight text-[#201a14] sm:text-4xl">
                AI CFO Takes The Helm
              </p>
              <p className="max-w-2xl text-base italic text-[#4d4134] sm:text-lg lg:pr-8">
                Transforming financial management for ERPNext teams.
              </p>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#a88a60] bg-[#fff4df] px-4 py-1 text-[11px] font-bold uppercase tracking-[0.18em] text-[#8c5c19]">
                Always watching your runway
              </p>
            </div>

            <div className="relative mx-auto w-full max-w-md rotate-[-1deg] border-[3px] border-[#2f2820] bg-[#efe1c9] p-3 shadow-[10px_10px_0_rgba(47,40,32,0.18)]">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.55),transparent_26%),radial-gradient(circle_at_75%_30%,rgba(63,77,92,0.2),transparent_24%),linear-gradient(145deg,rgba(33,27,21,0.12),transparent_45%,rgba(33,27,21,0.14))]" />
              <div className="relative overflow-hidden border-2 border-[#2f2820] bg-[#1d1b18]">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_28%,rgba(255,255,255,0.85),transparent_14%),radial-gradient(circle_at_72%_64%,rgba(255,255,255,0.22),transparent_18%),repeating-radial-gradient(circle_at_center,rgba(255,255,255,0.16)_0,rgba(255,255,255,0.16)_1px,transparent_1px,transparent_6px)] opacity-40 mix-blend-screen" />
                <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(247,239,223,0.1),transparent_35%,rgba(247,239,223,0.05)_65%,transparent)]" />
                <div className="relative grid min-h-[240px] place-items-end bg-[radial-gradient(circle_at_40%_32%,rgba(189,167,122,0.88),rgba(84,70,54,0.9)_42%,rgba(25,23,19,1)_100%)] px-4 py-4">
                  <div className="w-full border-t-2 border-[#f3e5c7] pt-3 text-[#f7eedf]">
                    <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#ecd9b0]">Front Page Photograph</p>
                    <p className="mt-1 text-lg font-serif font-bold uppercase leading-none">Runway Under Watch</p>
                    <p className="mt-2 text-xs leading-relaxed text-[#f5ecd9]">
                      Halftone detail, newspaper grit, and a CFO built to keep the cash horizon in view.
                    </p>
                  </div>
                </div>
              </div>
              <div className="absolute -left-2 top-6 h-10 w-10 rotate-12 border border-[#2f2820] bg-[#d7c19a] shadow-[0_4px_0_rgba(47,40,32,0.15)]" />
              <div className="absolute -right-3 bottom-6 h-14 w-14 -rotate-6 border border-[#2f2820] bg-[#c9a877] shadow-[0_4px_0_rgba(47,40,32,0.15)]" />
            </div>
          </div>

          <div className="mt-5 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center border-2 border-[#2f2820] bg-[#1c1712] px-8 py-3 text-sm font-bold uppercase tracking-[0.14em] text-[#f7efdf] transition-colors hover:bg-[#31281f]"
            >
              Open Vireon Dashboard
            </Link>
            <Link
              href="/runway"
              className="inline-flex items-center justify-center border-2 border-[#2f2820] bg-[#f8f0e2] px-8 py-3 text-sm font-bold uppercase tracking-[0.14em] text-[#201a14] transition-colors hover:bg-[#efe1c8]"
            >
              View Runway Forecast
            </Link>
          </div>
        </header>

        <section className="border-b-2 border-[#2f2820] bg-[#f1e6d2]">
          <div className="border-b-2 border-[#2f2820] px-5 py-2 text-center text-[11px] font-bold uppercase tracking-[0.18em] text-[#5a4a3a] sm:px-8">
            Front Page Articles
          </div>
          <div className="grid gap-0 md:grid-cols-3">
            {frontPageStories.map((item, index) => (
              <article
                key={item.title}
                className={`relative p-5 sm:p-6 ${index < frontPageStories.length - 1 ? "border-b-2 border-[#2f2820] md:border-b-0 md:border-r-2" : ""}`}
              >
                <div className="absolute right-4 top-4 h-10 w-10 rounded-full border border-[#2f2820] bg-[radial-gradient(circle,rgba(35,28,22,0.8)_0,rgba(35,28,22,0.8)_18%,transparent_18%,transparent_40%,rgba(35,28,22,0.8)_40%,rgba(35,28,22,0.8)_58%,transparent_58%)] opacity-60" />
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#855b29]">{item.kicker}</p>
                <h2 className="mt-2 max-w-[12ch] font-serif text-3xl font-bold uppercase leading-[0.95] text-[#1d1712]">{item.title}</h2>
                <p className="mt-2 text-sm leading-relaxed text-[#3f352a]">{item.blurb}</p>
                <div className="mt-5 border-t border-dashed border-[#7b6c59] pt-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-[#5d4f40]">
                  See the dashboard edition
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="grid gap-0 border-b-2 border-[#2f2820] lg:grid-cols-[1.15fr_0.9fr_0.95fr]">
          {highlights.map((item, index) => (
            <article
              key={item.title}
              className={`p-5 sm:p-6 ${index < highlights.length - 1 ? "border-b-2 border-[#2f2820] md:border-b-0 md:border-r-2" : ""}`}
            >
              <div className="mb-4 flex items-center gap-3 border-b-2 border-[#2f2820] pb-3">
                <span className="inline-flex h-9 w-9 items-center justify-center border-2 border-[#2f2820] bg-[#1c1712] text-[11px] font-bold uppercase tracking-[0.12em] text-[#f7efdf]">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#855b29]">Feature {index + 1}</p>
                  <p className="text-xs uppercase tracking-[0.08em] text-[#6a5948]">{item.subtitle}</p>
                </div>
              </div>
              <h3 className="font-serif text-2xl font-bold uppercase leading-tight text-[#1d1712]">{item.title}</h3>
              <p className="mt-4 text-sm leading-relaxed text-[#3f352a]">{item.blurb}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-0 border-b-2 border-[#2f2820] bg-[#f0e5d1] lg:grid-cols-[1.1fr_1fr_1fr]">
          <article className="border-b-2 border-[#2f2820] p-5 sm:p-6 lg:border-b-0 lg:border-r-2">
            <div className="inline-block border-b-4 border-[#7d1e1e] pb-2">
              <h3 className="font-serif text-3xl font-bold uppercase text-[#7d1e1e]">Anomaly Detected</h3>
            </div>
            <div className="mt-4 border-2 border-[#2f2820] bg-[#efe4d1] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.5)]">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#4f4336]">AI Chat Insight</p>
              <p className="mt-3 text-sm leading-relaxed text-[#2d251d]">&quot;Why did expenses spike last month?&quot;</p>
              <p className="mt-2 text-sm leading-relaxed text-[#2d251d]">
                Spend rose on marketing and cloud usage. Vireon flags the delta and recommends corrective actions.
              </p>
              <p className="mt-4 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#5d4f40]">Detailed analysis in dashboard</p>
            </div>
          </article>

          <article className="border-b-2 border-[#2f2820] p-5 sm:p-6 lg:border-b-0 lg:border-r-2">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#4f4336]">Alert: Spike in Expenses</p>
            <p className="mt-3 font-serif text-5xl font-bold text-[#9b231f]">45%</p>
            <p className="mt-1 text-sm uppercase tracking-[0.1em] text-[#5d4f40]">vs average baseline</p>

            <div className="mt-5 flex h-32 items-end gap-2 border-t border-[#9b8a73] pt-4">
              {[28, 32, 30, 36, 40, 42, 46, 44, 49, 52, 57, 35].map((bar, idx) => (
                <div
                  key={idx}
                  className="flex-1 bg-[#465a72] shadow-[0_-1px_0_rgba(255,255,255,0.22)]"
                  style={{ height: `${bar * 1.8}px` }}
                />
              ))}
            </div>
          </article>

          <article className="relative overflow-hidden p-5 sm:p-6">
            <div className="absolute right-0 top-0 h-24 w-24 rounded-bl-[2rem] bg-[radial-gradient(circle_at_30%_30%,rgba(124,96,58,0.26),transparent_35%),repeating-linear-gradient(135deg,rgba(255,255,255,0.32)_0,rgba(255,255,255,0.32)_2px,transparent_2px,transparent_8px)] opacity-70" />
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#4f4336]">Runway Forecast</p>
            <p className="mt-4 text-sm uppercase tracking-[0.08em] text-[#5d4f40]">Cash Remaining</p>
            <p className="font-serif text-5xl font-bold text-[#18130f]">$790K</p>
            <p className="mt-4 text-sm uppercase tracking-[0.08em] text-[#5d4f40]">Runway</p>
            <p className="font-serif text-5xl font-bold text-[#18130f]">5.2</p>
            <p className="mt-1 text-sm uppercase tracking-[0.08em] text-[#5d4f40]">Months</p>

            <Link
              href="/runway"
              className="mt-6 inline-flex border border-[#2f2820] bg-[#fff9ef] px-4 py-2 text-xs font-bold uppercase tracking-[0.12em] text-[#1f1913] transition-colors hover:bg-[#f0e4cf]"
            >
              Go to Runway
            </Link>
          </article>
        </section>

        <section className="border-b-2 border-[#2f2820] bg-[#f5eddc]">
          <div className="flex items-center justify-between border-b-2 border-[#2f2820] px-5 py-2 text-[11px] font-bold uppercase tracking-[0.18em] text-[#5a4a3a] sm:px-8">
            <span>Inside This Edition</span>
            <span>See page 2 for AI CFO insights</span>
          </div>
          <div className="grid gap-0 md:grid-cols-4">
          {[
            "Loan & Depreciation Calculations",
            "Multi-Currency Support in Progress",
            "PDF Reports Available",
            "Cloud Deployment with AWS + Ollama",
          ].map((line, index) => (
            <div
              key={line}
              className={`px-4 py-4 text-[11px] uppercase tracking-[0.1em] text-[#4d4134] ${index < 3 ? "border-b border-[#2f2820] md:border-b-0 md:border-r" : ""}`}
            >
              {line}
            </div>
          ))}
          </div>
        </section>

        <footer className="flex flex-col gap-3 px-5 py-4 text-[10px] uppercase tracking-[0.18em] text-[#66584b] sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <span>Vireon Times special report</span>
          <span>Built for founders, finance, and operators who need runway clarity</span>
        </footer>
      </div>
    </main>
  );
}
