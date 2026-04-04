"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function DashboardError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f6f3ee] px-6 py-12 text-[#1d1b17]">
      <div className="max-w-xl rounded-3xl border border-[#ebc1b8] bg-[#fff8f4] p-8 shadow-[0_18px_48px_rgba(63,45,24,0.1)]">
        <div className="flex items-center gap-3">
          <AlertTriangle className="h-6 w-6 text-[#9f3f30]" />
          <h1 className="text-2xl font-semibold text-[#2c2013]">Dashboard error</h1>
        </div>
        <p className="mt-3 text-sm text-[#5f5344]">
          Something on this dashboard failed to render. The app shell is still available, and you can retry the route.
        </p>
        <pre className="mt-4 overflow-auto rounded-2xl border border-[#ead9d0] bg-white p-4 text-xs text-[#7f6f63]">
          {error.message}
        </pre>
        <button
          onClick={reset}
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
        >
          <RefreshCw className="h-4 w-4" />
          Try again
        </button>
      </div>
    </div>
  );
}
