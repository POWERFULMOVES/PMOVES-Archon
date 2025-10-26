'use client';

import { createClientComponentClient, type SupabaseClient } from '@supabase/auth-helpers-nextjs';
import type { Database } from './database.types';

let browserClient: SupabaseClient<Database> | null = null;

export function getBrowserSupabaseClient(): SupabaseClient<Database> {
  if (!browserClient) {
    browserClient = createClientComponentClient<Database>() as unknown as SupabaseClient<Database>;
  }
  return browserClient;
}
