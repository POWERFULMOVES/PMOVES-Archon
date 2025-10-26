import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import type { Database } from './database.types';

type SupabaseClientOptions = {
  serviceRole?: boolean;
};

const ensureUrl = (): string => {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
  if (!url) {
    throw new Error(
      'SUPABASE_URL (or NEXT_PUBLIC_SUPABASE_URL) is not configured. Run `make supa-start` + `make supa-status` and sync the values into pmoves/.env.local.'
    );
  }
  return url;
};

const ensureAnonKey = (): string => {
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY;
  if (!key) {
    throw new Error(
      'SUPABASE_ANON_KEY (or NEXT_PUBLIC_SUPABASE_ANON_KEY) is missing. Export the publishable key from `make supa-status` and add it to pmoves/.env.local.'
    );
  }
  return key;
};

const ensureServiceRoleKey = (): string => {
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!key) {
    throw new Error(
      'SUPABASE_SERVICE_ROLE_KEY is missing. Copy the service role key from `make supa-status` into pmoves/.env.local before using server-side helpers.'
    );
  }
  return key;
};

let cachedBrowserClient: SupabaseClient<Database> | null = null;
let cachedRestUrl: string | null = null;

export type TypedSupabaseClient = SupabaseClient<Database>;

export const createSupabaseBrowserClient = (): TypedSupabaseClient =>
  createClient<Database>(ensureUrl(), ensureAnonKey(), {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
    },
  });

export const getSupabaseBrowserClient = (): TypedSupabaseClient => {
  if (!cachedBrowserClient) {
    cachedBrowserClient = createSupabaseBrowserClient();
  }
  return cachedBrowserClient;
};

export const getSupabaseRestUrl = (): string => {
  if (cachedRestUrl) {
    return cachedRestUrl;
  }
  const explicit = process.env.NEXT_PUBLIC_SUPABASE_REST_URL || process.env.SUPABASE_REST_URL;
  if (explicit) {
    cachedRestUrl = explicit.replace(/\/$/, '');
    return cachedRestUrl;
  }
  cachedRestUrl = `${ensureUrl().replace(/\/$/, '')}/rest/v1`;
  return cachedRestUrl;
};

export const createSupabaseServerClient = (
  options: SupabaseClientOptions = {}
): TypedSupabaseClient => {
  const { serviceRole = false } = options;
  const key = serviceRole ? ensureServiceRoleKey() : ensureAnonKey();
  return createClient<Database>(ensureUrl(), key, {
    auth: {
      autoRefreshToken: !serviceRole,
      persistSession: false,
    },
  });
};

export const createSupabaseServiceRoleClient = (): TypedSupabaseClient =>
  createSupabaseServerClient({ serviceRole: true });
