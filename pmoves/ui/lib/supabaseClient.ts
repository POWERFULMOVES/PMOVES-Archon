import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { uiConfig } from "@/config";
import type { Database } from "./database.types";

type SupabaseClientOptions = {
  serviceRole?: boolean;
};

const { supabaseUrl, supabaseAnonKey, supabaseServiceRoleKey } = uiConfig;

const ensureAnonKey = () => {
  if (!supabaseAnonKey) {
    throw new Error(
      "SUPABASE_ANON_KEY (or NEXT_PUBLIC_SUPABASE_ANON_KEY) is not configured. Run `make supa-status` after `make supa-start` and copy the publishable key into pmoves/.env.local."
    );
  }
  return supabaseAnonKey;
};

const ensureServiceRoleKey = () => {
  if (!supabaseServiceRoleKey) {
    throw new Error(
      "SUPABASE_SERVICE_ROLE_KEY is missing. Export the service role key from `make supa-status` and add it to pmoves/.env.local before using server-side helpers."
    );
  }
  return supabaseServiceRoleKey;
};

const ensureUrl = () => {
  if (!supabaseUrl) {
    throw new Error(
      "SUPABASE_URL (or NEXT_PUBLIC_SUPABASE_URL) is not configured. Populate pmoves/.env.local via the Supabase CLI bring-up documented in pmoves/docs/LOCAL_DEV.md."
    );
  }
  return supabaseUrl;
};

export type TypedSupabaseClient = SupabaseClient<Database>;

export const createSupabaseBrowserClient = (): TypedSupabaseClient => {
  return createClient<Database>(ensureUrl(), ensureAnonKey(), {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
    },
  });
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
