#!/usr/bin/env bun
/**
 * Regenerates the SQLite schema vintage fixtures in
 * packages/core/src/db/fixtures/sqlite-vintages/ from release tags.
 *
 * One fixture per DISTINCT schema ever shipped: the DDL that `createSchema()`
 * executed on that release's fresh install. sqlite-vintages.test.ts replays each
 * fixture into an empty database, opens it with the current SqliteAdapter, and
 * asserts the upgrade converges on the fresh-install shape — the SQLite mirror
 * of check:schema-upgrades.
 *
 * Extraction is textual on purpose. `createSchema()` is, in every released tag,
 * a single uninterpolated backtick literal, so slicing it out of
 * `git show <tag>:…/sqlite.ts` recovers the vintage DDL exactly — without
 * checking out each tag or executing old code against its own dependency tree.
 * That single-literal shape is this extractor's validity condition: if the
 * extracted text ever contains `${…}` or the signature can no longer be found,
 * this script FAILS instead of writing a wrong fixture. The fix is a deliberate
 * extractor change, never a workaround.
 *
 * Fixtures are checked in (unlike the Postgres baselines, read at CI time)
 * because the test that consumes them must also run in the shallow checkout of
 * the `test` job, where tags do not exist.
 *
 * Usage:
 *   bun run scripts/generate-sqlite-vintages.ts          # write
 *   bun run scripts/generate-sqlite-vintages.ts --check  # verify (exit 2 if stale)
 *
 * Exit codes:
 *   0  fixtures generated (and unchanged, if --check)
 *   1  unexpected error (extraction failed, git failed, etc.)
 *   2  --check was passed and the fixture set would change
 */
import { spawnSync } from 'child_process';
import { mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'fs';
import { join, resolve } from 'path';

const REPO_ROOT = resolve(import.meta.dir, '..');
const ADAPTER_REPO_PATH = 'packages/core/src/db/adapters/sqlite.ts';
const FIXTURES_DIR = join(REPO_ROOT, 'packages/core/src/db/fixtures/sqlite-vintages');
const CHECK_ONLY = process.argv.includes('--check');
const SCHEMA_SIGNATURE = 'private createSchema(): void {';

/**
 * Deliberately `spawnSync` rather than `@archon/git`: this script must run in the
 * `schema-upgrade` CI job with no `bun install` (it imports nothing outside Node
 * builtins), and reads history — `git show <ref>:<path>` — rather than
 * manipulating worktrees, which is what `@archon/git` covers. The argument array
 * means no ref ever reaches a shell.
 */
function git(...args: string[]): { ok: boolean; stdout: string; stderr: string } {
  const r = spawnSync('git', args, { encoding: 'utf8', cwd: REPO_ROOT });
  if (r.error) throw new Error(`git could not be executed: ${r.error.message}`);
  return { ok: r.status === 0, stdout: r.stdout ?? '', stderr: r.stderr ?? '' };
}

/**
 * Recover the exact SQL `createSchema()` ran on `tag`.
 *
 * The schema lives between the first backtick after the method signature and the
 * next backtick. A `${` inside that span means the "schema is one static
 * literal" premise is broken and extraction would be silently unfaithful —
 * refuse rather than emit a fixture nobody could trust.
 */
function extractSchemaSql(tag: string): string {
  const show = git('show', `${tag}:${ADAPTER_REPO_PATH}`);
  if (!show.ok) throw new Error(`${tag}: cannot read ${ADAPTER_REPO_PATH} (broken tag?)`);

  const sigAt = show.stdout.indexOf(SCHEMA_SIGNATURE);
  if (sigAt === -1) {
    throw new Error(`${tag}: ${SCHEMA_SIGNATURE} not found — extractor must be revisited`);
  }
  const start = show.stdout.indexOf('`', sigAt + SCHEMA_SIGNATURE.length);
  const end = start === -1 ? -1 : show.stdout.indexOf('`', start + 1);
  if (start === -1 || end === -1) {
    throw new Error(
      `${tag}: createSchema() is not a single backtick literal — extractor must be revisited`
    );
  }

  const sql = show.stdout.slice(start + 1, end);
  if (sql.includes('${')) {
    throw new Error(
      `${tag}: extracted schema contains \${…} interpolation — the single-literal premise is broken, extractor must be revisited`
    );
  }
  return sql;
}

/**
 * Every DISTINCT schema ever shipped in a release tag, oldest tag per version.
 *
 * A release that does not touch the schema ships the same SQL as the one before
 * it, so deduplicating by content makes this the set of vintages a real install
 * can actually have, rather than a sample of recent releases.
 */
function vintages(): Map<string, string> {
  const tagResult = git('tag', '--sort=creatordate');
  if (!tagResult.ok) {
    throw new Error(`git tag failed: ${tagResult.stderr.trim() || '(no stderr)'}`);
  }
  const tags = tagResult.stdout.split('\n').filter(Boolean);
  if (tags.length === 0) {
    // An empty tag set would make write mode delete every checked-in fixture
    // while exiting 0; no release history means this script cannot run.
    throw new Error(
      'git tag listed no tags — cannot regenerate vintage fixtures (shallow or broken checkout?)'
    );
  }
  const oldestTagPerSchema = new Map<string, string>();
  let withoutAdapter = 0;

  // Tags are sorted oldest-first, and the adapter file has existed continuously
  // in every release since it was introduced. So a rev-parse miss on a tag that
  // follows tags carrying the file is not "predates the adapter" — the file was
  // moved or renamed and extraction would silently end vintage coverage.
  let seenAdapter = false;

  for (const tag of tags) {
    const present = git('rev-parse', `${tag}:${ADAPTER_REPO_PATH}`);
    if (!present.ok) {
      if (seenAdapter) {
        throw new Error(
          `${tag}: ${ADAPTER_REPO_PATH} is missing from a tag newer than tags that carry it — ` +
            'the adapter file was likely moved or renamed; extractor must be revisited'
        );
      }
      withoutAdapter++;
      continue;
    }
    seenAdapter = true;
    const sql = extractSchemaSql(tag);
    if (!oldestTagPerSchema.has(sql)) oldestTagPerSchema.set(sql, tag);
  }

  if (withoutAdapter > 0) {
    console.log(
      `note: ${withoutAdapter} tag(s) predate ${ADAPTER_REPO_PATH} and cannot be a vintage`
    );
  }
  console.log(
    `note: ${tags.length - withoutAdapter} tag(s) carry ${oldestTagPerSchema.size} distinct schema version(s)`
  );
  return oldestTagPerSchema;
}

/** Fixture filename for a tag. Tags are `vX.Y.Z`, so the name is injection-safe. */
function fixtureName(tag: string): string {
  if (!/^v[\w.-]+$/.test(tag)) throw new Error(`unexpected tag shape: ${tag}`);
  return `${tag}.sql`;
}

function main(): void {
  const expected = new Map<string, string>();
  for (const [sql, tag] of vintages()) expected.set(fixtureName(tag), sql);

  // No-exist is the normal first run; recursive keeps this idempotent afterwards.
  mkdirSync(FIXTURES_DIR, { recursive: true });
  const existing = new Set(readdirSync(FIXTURES_DIR).filter(f => f.endsWith('.sql')));

  const changed: string[] = [];
  for (const [name, sql] of expected) {
    let current: string | undefined;
    try {
      current = readFileSync(join(FIXTURES_DIR, name), 'utf8');
    } catch {
      // missing fixture = change
    }
    if (current !== sql) changed.push(name);
  }
  for (const name of existing) {
    if (!expected.has(name)) changed.push(name);
  }

  if (CHECK_ONLY) {
    if (changed.length > 0) {
      console.error(`sqlite vintage fixtures are stale (changed: ${changed.join(', ')}).`);
      console.error('Run: bun run generate:sqlite-vintages');
      process.exit(2);
    }
    console.log(`sqlite vintage fixtures are up to date (${expected.size} vintage(s)).`);
    return;
  }

  for (const name of existing) {
    if (!expected.has(name)) {
      rmSync(join(FIXTURES_DIR, name));
      console.log(`removed ${name} (vintage no longer exists)`);
    }
  }
  for (const [name, sql] of expected) {
    if (changed.includes(name)) {
      writeFileSync(join(FIXTURES_DIR, name), sql, 'utf8');
      console.log(`wrote ${name}`);
    }
  }
  console.log(`sqlite vintage fixtures up to date (${expected.size} vintage(s)).`);
}

try {
  main();
} catch (err: unknown) {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
}
