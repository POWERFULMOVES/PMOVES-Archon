/**
 * Regression test for the deliver pack's final `flip-ready` check-state read.
 *
 * The node's bash body is the unit under test: fixtures stub `flip-ready`'s
 * output directly, so no fixture can observe a failed `gh` read. This test
 * extracts the live bash body from the workflow YAML, substitutes the one
 * template reference, and runs it against fake `gh` and `git` executables so a
 * failed check read must refuse before `gh pr ready` is invoked.
 */
import { describe, expect, it } from 'bun:test';
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { trackTempRoots } from '@archon/paths/test-utils';

const WORKFLOW_YAML = resolve(
  import.meta.dir,
  '../../workflows/sdlc/deliver/archon-deliver.yaml'
);

const trackTempRoot = trackTempRoots();

function flipReadyBash(): string {
  const parsed = Bun.YAML.parse(readFileSync(WORKFLOW_YAML, 'utf8'));
  const node = (parsed as { nodes?: { id?: string; bash?: unknown }[] }).nodes?.find(
    entry => entry.id === 'flip-ready'
  );
  if (typeof node?.bash !== 'string') {
    throw new Error(`flip-ready node with a bash body not found in ${WORKFLOW_YAML}`);
  }
  return node.bash.replace('$pr.output.number', '42');
}

interface FakeGh {
  /** stdout when `gh api graphql` succeeds; omit for empty output. */
  graphqlOut?: string;
  /** stderr when `gh api graphql` fails (exit 1); omit for success. */
  graphqlFail?: string;
  /** stdout when `gh pr checks` succeeds; omit for empty output. */
  checksOut?: string;
  /** stderr when `gh pr checks` fails (exit 1); omit for success. */
  checksFail?: string;
}

function runFlipReady(gh: FakeGh): {
  code: number;
  stdout: string;
  stderr: string;
  readyCalled: boolean;
} {
  const root = trackTempRoot(mkdtempSync(join(tmpdir(), 'flip-ready-')));
  const bin = join(root, 'bin');
  mkdirSync(bin);
  const marker = join(root, 'ready-marker');

  const ghScript = `#!/bin/sh
if [ "$1" = "api" ] && [ "$2" = "graphql" ]; then
  if [ -n '${gh.graphqlFail ?? ''}' ]; then echo '${gh.graphqlFail ?? ''}' >&2; exit 1; fi
  printf '%s' '${gh.graphqlOut ?? ''}'
  exit 0
fi
if [ "$1" = "pr" ] && [ "$2" = "checks" ]; then
  if [ -n '${gh.checksFail ?? ''}' ]; then echo '${gh.checksFail ?? ''}' >&2; exit 1; fi
  printf '%s' '${gh.checksOut ?? ''}'
  exit 0
fi
if [ "$1" = "pr" ] && [ "$2" = "ready" ]; then
  : > '${marker}'
  echo "PR is ready"
  exit 0
fi
if [ "$1" = "pr" ] && [ "$2" = "view" ]; then
  case "$*" in
    *'--json isDraft'*) echo "false"; exit 0 ;;
    *'--json url'*) echo "https://github.com/example/repo/pull/42"; exit 0 ;;
  esac
  echo "fake gh: unexpected pr view args: $*" >&2
  exit 1
fi
echo "fake gh: unexpected args: $*" >&2
exit 1
`;
  writeFileSync(join(bin, 'gh'), ghScript);
  chmodSync(join(bin, 'gh'), 0o755);

  const gitScript = `#!/bin/sh
if [ "$1" = "remote" ] && [ "$2" = "get-url" ] && [ "$3" = "origin" ]; then
  echo "https://github.com/example/repo.git"
  exit 0
fi
echo "fake git: unexpected args: $*" >&2
exit 1
`;
  writeFileSync(join(bin, 'git'), gitScript);
  chmodSync(join(bin, 'git'), 0o755);

  const result = spawnSync('bash', ['-c', flipReadyBash()], {
    env: { ...process.env, PATH: `${bin}:${process.env.PATH ?? ''}` },
    encoding: 'utf8',
  });

  return {
    code: result.status ?? -1,
    stdout: result.stdout ?? '',
    stderr: result.stderr ?? '',
    readyCalled: existsSync(marker),
  };
}

describe('flip-ready check-state read', () => {
  it('refuses before the ready flip when the check read fails', () => {
    const result = runFlipReady({
      graphqlFail: 'GraphQL: could not resolve to a Repository',
      checksFail: 'GraphQL: could not resolve to a Repository',
    });

    expect(result.readyCalled).toBe(false);
    expect(result.code).not.toBe(0);
    expect(result.stderr).toContain('flip-ready');
  });

  it('proceeds on a successfully observed empty check set (no CI)', () => {
    const result = runFlipReady({ graphqlOut: '0' });

    expect(result.code).toBe(0);
    expect(result.readyCalled).toBe(true);
    expect(result.stdout.trim()).toBe('https://github.com/example/repo/pull/42');
  });

  it('refuses with the non-green check names when checks are not green', () => {
    const result = runFlipReady({
      graphqlOut: '1',
      checksOut: 'build (fail)\nunit (pending)',
    });

    expect(result.readyCalled).toBe(false);
    expect(result.code).not.toBe(0);
    expect(result.stderr).toContain('build (fail)');
    expect(result.stderr).toContain('unit (pending)');
  });

  it('proceeds when every observed check is green or skipped', () => {
    const result = runFlipReady({ graphqlOut: '2', checksOut: '' });

    expect(result.code).toBe(0);
    expect(result.readyCalled).toBe(true);
  });

  it('refuses when checks exist but their classification read fails', () => {
    const result = runFlipReady({
      graphqlOut: '1',
      checksFail: 'GraphQL: could not resolve to a PullRequest',
    });

    expect(result.readyCalled).toBe(false);
    expect(result.code).not.toBe(0);
    expect(result.stderr).toContain('flip-ready');
  });
});
