import Link from "next/link";
import { ArrowRight, Activity, ShieldCheck, Zap } from "lucide-react";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-50 font-sans selection:bg-indigo-500/30">
      {/* Navbar Pattern */}
      <header className="absolute inset-x-0 top-0 z-50 flex items-center justify-between p-6 lg:px-8">
        <div className="flex lg:flex-1">
          <Link href="/" className="-m-1.5 p-1.5 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-indigo-500 text-white font-bold">
              V
            </div>
            <span className="font-semibold tracking-tight text-xl">Vireon</span>
          </Link>
        </div>
        <div className="flex flex-1 justify-end">
          <Link
            href="/dashboard"
            className="text-sm font-semibold leading-6 text-zinc-200 hover:text-white transition-colors"
          >
            Log in <span aria-hidden="true">&rarr;</span>
          </Link>
        </div>
      </header>

      <main className="relative isolate flex-grow flex flex-col items-center justify-center px-6 pt-14 lg:px-8">
        {/* Decorative Background Blob */}
        <div
          className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80"
          aria-hidden="true"
        >
          <div
            className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-20 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]"
            style={{
              clipPath:
                "polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)",
            }}
          />
        </div>

        <div className="mx-auto max-w-3xl py-32 sm:py-48 lg:py-56 text-center">
          <div className="mb-8 flex justify-center">
            <div className="relative rounded-full px-3 py-1 text-sm leading-6 text-zinc-400 ring-1 ring-white/10 hover:ring-white/20 transition-all">
              Announcing our new ERPNext Integration.{" "}
              <Link href="/dashboard" className="font-semibold text-indigo-400">
                <span className="absolute inset-0" aria-hidden="true" />
                Read more <span aria-hidden="true">&rarr;</span>
              </Link>
            </div>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-6xl drop-shadow-sm">
            AI-Powered Financial Intelligence for Scale-ups
          </h1>
          <p className="mt-6 text-lg leading-8 text-zinc-300 max-w-2xl mx-auto">
            Vireon is your Agentic CFO. Connect automatically to your ERP to run runway simulations,
            detect massive spending anomalies, and chat intuitively with your financial data.
          </p>
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <Link
              href="/dashboard"
              className="group rounded-full bg-indigo-500 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-400 transition-all flex items-center gap-2"
            >
              Enter Dashboard
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
            <Link href="#features" className="text-sm font-semibold leading-6 text-zinc-200 hover:text-white transition-colors">
              Learn more <span aria-hidden="true">↓</span>
            </Link>
          </div>
        </div>

        {/* Features Preview Section */}
        <div id="features" className="mx-auto max-w-5xl px-6 pb-24 sm:pb-32 lg:px-8">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
            {[
              {
                title: "Runway Simulations",
                description: "Predict the exact impact of hiring 10 new engineers on your cash flow before you send the offers.",
                icon: Activity,
              },
              {
                title: "Anomaly Detection",
                description: "Our core math engine automatically flags massive vendor spikes and duplicate invoice billings.",
                icon: ShieldCheck,
              },
              {
                title: "Agentic AI Analysis",
                description: "Chat directly with an AI CFO that understands your runway, burn rates, and financial limits.",
                icon: Zap,
              },
            ].map((feature, i) => (
              <div key={i} className="flex flex-col items-center sm:items-start text-center sm:text-left p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800 backdrop-blur-sm">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-500/10">
                  <feature.icon className="h-6 w-6 text-indigo-400" />
                </div>
                <h3 className="text-lg font-semibold text-white">{feature.title}</h3>
                <p className="mt-2 text-sm text-zinc-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
