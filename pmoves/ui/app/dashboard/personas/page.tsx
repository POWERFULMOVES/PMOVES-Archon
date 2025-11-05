import Link from 'next/link';
import { getServiceSupabaseClient } from '@/lib/supabaseServer';

export const dynamic = 'force-dynamic';

type Persona = {
  name: string;
  version: string | number | null;
  description: string | null;
  runtime: Record<string, any> | null;
};

async function loadPersonas(): Promise<{ data: Persona[]; error?: string }>
{
  try {
    const client = getServiceSupabaseClient();
    // Prefer explicit schema to avoid collisions
    const { data, error } = await client
      .schema('pmoves_core')
      .from('personas')
      .select('name, version, description, runtime')
      .order('name')
      .limit(100);
    if (error) return { data: [], error: error.message };
    return { data: data as Persona[] };
  } catch (e: any) {
    return { data: [], error: e?.message || 'Unexpected error' };
  }
}

export default async function PersonasPage() {
  const { data, error } = await loadPersonas();
  return (
    <main className="mx-auto max-w-5xl p-6">
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Grounded Personas</h1>
        <Link href="/" className="text-sm text-slate-600 hover:text-slate-900">
          ← Back to console
        </Link>
      </header>
      {error && (
        <div className="mb-4 rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          Unable to fetch personas from Supabase REST. If you are using the Supabase CLI
          PostgREST (65421) and it doesn’t expose the pmoves_core schema, either:
          <ul className="ml-5 list-disc">
            <li>Set <code>SUPABASE_SERVICE_URL</code> to a PostgREST endpoint configured with <code>public,pmoves_core</code>.</li>
            <li>Or run the compose PostgREST on 3010 and point the service client there.</li>
          </ul>
          Error: {error}
        </div>
      )}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {data.map((p) => (
          <div key={`${p.name}-${p.version}`} className="rounded border border-slate-200 bg-white p-4 shadow-sm">
            <h2 className="text-lg font-medium text-slate-900">
              {p.name} <span className="ml-2 text-xs text-slate-500">v{String(p.version ?? '')}</span>
            </h2>
            {p.description && (
              <p className="mt-2 text-sm text-slate-600">{p.description}</p>
            )}
            {p.runtime && (
              <pre className="mt-3 overflow-x-auto rounded bg-slate-50 p-2 text-xs text-slate-700">
                {JSON.stringify(p.runtime, null, 2)}
              </pre>
            )}
          </div>
        ))}
        {!error && data.length === 0 && (
          <div className="rounded border border-slate-200 bg-white p-4 text-sm text-slate-600">
            No personas found yet. Re-run <code>make -C pmoves supabase-bootstrap</code> to seed v5.12 definitions.
          </div>
        )}
      </section>
    </main>
  );
}

