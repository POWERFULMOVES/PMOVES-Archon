-- Archon prompt catalog
-- Ensures Supabase exposes `public.archon_prompts` so Archon can load prompt
-- definitions without triggering PostgREST 205 warnings. The table mirrors
-- the upstream schema but keeps the seed data optional; PMOVES can populate
-- rows via the UI or follow-up migrations as workflows evolve.

set search_path = public;

-- Keep the timestamp helper in sync with upstream expectations.
create or replace function update_updated_at_column()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table if not exists archon_prompts (
  id uuid primary key default gen_random_uuid(),
  prompt_name text unique not null,
  prompt text not null,
  description text,
  created_at timestamptz default timezone('utc', now()),
  updated_at timestamptz default timezone('utc', now())
);

create index if not exists idx_archon_prompts_name
  on archon_prompts(prompt_name);

drop trigger if exists update_archon_prompts_updated_at on archon_prompts;
create trigger update_archon_prompts_updated_at
  before update on archon_prompts
  for each row execute function update_updated_at_column();

alter table archon_prompts enable row level security;

drop policy if exists "Allow service role full access to archon_prompts" on archon_prompts;
create policy "Allow service role full access to archon_prompts" on archon_prompts
  for all
  using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

drop policy if exists "Allow authenticated users to read archon_prompts" on archon_prompts;
create policy "Allow authenticated users to read archon_prompts" on archon_prompts
  for select
  to authenticated
  using (true);

-- Optional seed rows stay in follow-up migrations; the empty table unblocks
-- Archon's prompt loader while giving PMOVES control over which prompts ship.
