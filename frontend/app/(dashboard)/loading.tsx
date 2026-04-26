export default function DashboardLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f6f3ee] px-6 py-12 text-[#1d1b17]">
      <div className="w-full max-w-4xl space-y-4 rounded-3xl border border-[#ddd2c4] bg-[#fffdf8] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.08)]">
        <div className="h-8 w-56 animate-pulse rounded-full bg-[#e8dccd]" />
        <div className="grid gap-4 md:grid-cols-3">
          <div className="h-24 animate-pulse rounded-2xl bg-[#efe4d7]" />
          <div className="h-24 animate-pulse rounded-2xl bg-[#efe4d7]" />
          <div className="h-24 animate-pulse rounded-2xl bg-[#efe4d7]" />
        </div>
        <div className="h-72 animate-pulse rounded-3xl bg-[#efe4d7]" />
      </div>
    </div>
  );
}
