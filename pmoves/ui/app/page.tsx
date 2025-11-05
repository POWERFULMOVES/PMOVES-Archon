import Link from 'next/link';

export default function HomePage() {
  const hasBootJwt = Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_BOOT_USER_JWT || process.env.SUPABASE_BOOT_USER_JWT
  );
  const primaryHref = hasBootJwt ? '/dashboard/ingest' : '/login';
  const primaryLabel = hasBootJwt ? 'Open dashboard' : 'Continue to login';
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-slate-100 p-8 text-center">
      <div className="space-y-3">
        <h1 className="text-3xl font-semibold text-slate-900">PMOVES Operator Console</h1>
        <p className="max-w-md text-sm text-slate-600">
          Sign in to manage ingestion workflows, upload new assets, and monitor Supabase processing pipelines.
        </p>
      </div>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Link
          href={primaryHref}
          className="rounded bg-slate-900 px-5 py-2 text-sm font-semibold text-white shadow hover:bg-slate-700"
        >
          {primaryLabel}
        </Link>
        <Link
          href="/dashboard/ingest"
          className="rounded border border-slate-300 px-5 py-2 text-sm font-semibold text-slate-700 hover:border-slate-400 hover:text-slate-900"
        >
          View ingestion dashboard
        </Link>
      </div>
    </main>
  );
}
