import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let browserClient: SupabaseClient | null = null;

interface ClientOptions {
  url?: string;
  anonKey?: string;
}

const defaultOptions: ClientOptions = {
  url:
    process.env.NEXT_PUBLIC_SUPABASE_URL?.trim() ||
    process.env.SUPABASE_URL?.trim(),
  anonKey:
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim() ||
    process.env.SUPABASE_ANON_KEY?.trim(),
};

export function getSupabaseBrowserClient(
  opts: ClientOptions = {}
): SupabaseClient {
  if (browserClient) {
    return browserClient;
  }

  const url = (opts.url ?? defaultOptions.url) || "";
  const anonKey = (opts.anonKey ?? defaultOptions.anonKey) || "";

  if (!url || !anonKey) {
    throw new Error(
      "Supabase client requires NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY (or server-side equivalents)."
    );
  }

  browserClient = createClient(url, anonKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  });

  return browserClient;
}

export function getSupabaseRestUrl(): string | null {
  const explicit =
    process.env.NEXT_PUBLIC_SUPABASE_REST_URL?.trim() ||
    process.env.SUPABASE_REST_URL?.trim();
  if (explicit) {
    return explicit.replace(/\/$/, "");
  }

  const url = defaultOptions.url;
  if (!url) {
    return null;
  }

  return `${url.replace(/\/$/, "")}/rest/v1`;
}
