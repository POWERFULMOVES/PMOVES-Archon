import { describe, test, expect, beforeEach, afterEach } from 'bun:test';
import { mkdir, readdir, rm, writeFile, readFile } from 'node:fs/promises';
import { basename, join } from 'node:path';
import { tmpdir } from 'node:os';
import { writeNodeArtifact, readNodeArtifacts, latestNodeArtifactOfType } from './artifacts-index';

describe('artifacts-index', () => {
  let dir: string;

  beforeEach(async () => {
    dir = join(tmpdir(), `artifacts-index-${Date.now()}-${Math.random().toString(36).slice(2)}`);
    await mkdir(dir, { recursive: true });
  });

  afterEach(async () => {
    await rm(dir, { recursive: true, force: true });
  });

  test('writeNodeArtifact writes the output file + metadata and returns the entry', async () => {
    const meta = await writeNodeArtifact(
      dir,
      {
        nodeId: 'planner',
        outputType: 'plan',
        runId: 'run-1',
        producedAt: '2026-06-03T00:00:00.000Z',
        sessionId: 'sess-1',
      },
      'the plan body'
    );

    expect(meta).toMatchObject({
      nodeId: 'planner',
      outputType: 'plan',
      path: join('nodes', 'planner.md'),
      runId: 'run-1',
      producedAt: '2026-06-03T00:00:00.000Z',
      sessionId: 'sess-1',
    });
    expect(meta.size).toBe(Buffer.byteLength('the plan body', 'utf8'));
    expect(await readFile(join(dir, 'nodes', 'planner.md'), 'utf8')).toBe('the plan body');
    const onDisk = JSON.parse(
      await readFile(join(dir, 'nodes', 'planner.meta.json'), 'utf8')
    ) as Record<string, unknown>;
    expect(onDisk.outputType).toBe('plan');
  });

  test('writeNodeArtifact omits sessionId when not provided', async () => {
    const meta = await writeNodeArtifact(
      dir,
      { nodeId: 'n', outputType: 'findings', runId: 'r', producedAt: '2026-06-03T00:00:00.000Z' },
      'x'
    );
    expect('sessionId' in meta).toBe(false);
  });

  test('loop_group lineages produce distinct stable artifact identities', async () => {
    const first = await writeNodeArtifact(
      dir,
      {
        nodeId: 'review',
        outputType: 'findings',
        loopGroupPath: [
          { groupId: 'outer', iteration: 1 },
          { groupId: 'inner', iteration: 1 },
        ],
        runId: 'r',
        producedAt: '2026-06-03T00:00:00.000Z',
      },
      'first'
    );
    const second = await writeNodeArtifact(
      dir,
      {
        nodeId: 'review',
        outputType: 'findings',
        loopGroupPath: [
          { groupId: 'outer', iteration: 2 },
          { groupId: 'inner', iteration: 1 },
        ],
        runId: 'r',
        producedAt: '2026-06-03T01:00:00.000Z',
      },
      'second'
    );

    expect(basename(first.path)).toMatch(/^loop\.[0-9a-f]{64}__review\.md$/);
    expect(basename(second.path)).toMatch(/^loop\.[0-9a-f]{64}__review\.md$/);
    expect(first.path).not.toBe(second.path);
    expect(await readFile(join(dir, first.path), 'utf8')).toBe('first');
    expect(await readFile(join(dir, second.path), 'utf8')).toBe('second');
    const artifacts = (await readNodeArtifacts(dir)).sort(
      (left, right) =>
        (left.loopGroupPath?.[0]?.iteration ?? 0) - (right.loopGroupPath?.[0]?.iteration ?? 0)
    );
    expect(artifacts.map(entry => entry.loopGroupPath)).toEqual([
      [
        { groupId: 'outer', iteration: 1 },
        { groupId: 'inner', iteration: 1 },
      ],
      [
        { groupId: 'outer', iteration: 2 },
        { groupId: 'inner', iteration: 1 },
      ],
    ]);
  });

  test('readNodeArtifacts returns [] for a dir with no artifacts yet', async () => {
    expect(await readNodeArtifacts(dir)).toEqual([]);
  });

  test('readNodeArtifacts skips corrupt meta files (non-fatal)', async () => {
    await writeNodeArtifact(
      dir,
      { nodeId: 'good', outputType: 'plan', runId: 'r', producedAt: '2026-06-03T00:00:00.000Z' },
      'ok'
    );
    await writeFile(join(dir, 'nodes', 'bad.meta.json'), '{ not valid json', 'utf8');

    const entries = await readNodeArtifacts(dir);
    expect(entries.map(e => e.nodeId)).toEqual(['good']);
  });

  test('latestNodeArtifactOfType returns the newest of a given type', async () => {
    await writeNodeArtifact(
      dir,
      { nodeId: 'a', outputType: 'plan', runId: 'r', producedAt: '2026-06-03T00:00:00.000Z' },
      'older'
    );
    await writeNodeArtifact(
      dir,
      { nodeId: 'b', outputType: 'plan', runId: 'r', producedAt: '2026-06-03T01:00:00.000Z' },
      'newer'
    );
    await writeNodeArtifact(
      dir,
      { nodeId: 'c', outputType: 'code', runId: 'r', producedAt: '2026-06-03T02:00:00.000Z' },
      'other'
    );

    const latest = await latestNodeArtifactOfType(dir, 'plan');
    expect(latest?.nodeId).toBe('b');
    expect(await latestNodeArtifactOfType(dir, 'missing')).toBeUndefined();
  });

  test('a node id with path separators is sanitized to a single safe segment', async () => {
    const meta = await writeNodeArtifact(
      dir,
      { nodeId: '../evil', outputType: 'plan', runId: 'r', producedAt: '2026-06-03T00:00:00.000Z' },
      'x'
    );
    expect(meta.path).toBe(join('nodes', '___evil.md'));
    expect(meta.path).not.toContain('..');
    // The original id is preserved in metadata even though the filename is sanitized.
    expect(meta.nodeId).toBe('../evil');
  });

  test('two distinct node ids that collide on the same safe segment fail loudly (no silent overwrite)', async () => {
    await writeNodeArtifact(
      dir,
      { nodeId: 'a.b', outputType: 'plan', runId: 'r', producedAt: '2026-06-03T00:00:00.000Z' },
      'first'
    );
    // `a.b` and `a_b` both sanitize to `a_b` — the second write must throw rather
    // than silently clobber the first node's artifact.
    await expect(
      writeNodeArtifact(
        dir,
        { nodeId: 'a_b', outputType: 'plan', runId: 'r', producedAt: '2026-06-03T00:01:00.000Z' },
        'second'
      )
    ).rejects.toThrow(/collision/);
    // First writer wins; its artifact is intact.
    expect(await readFile(join(dir, 'nodes', 'a_b.md'), 'utf8')).toBe('first');
    const entries = await readNodeArtifacts(dir);
    expect(entries.map(e => e.nodeId)).toEqual(['a.b']);
  });

  test('loop owner digests distinguish group ids that sanitize alike', async () => {
    const first = await writeNodeArtifact(
      dir,
      {
        nodeId: 'review',
        outputType: 'findings',
        loopGroupPath: [{ groupId: 'a.b', iteration: 1 }],
        runId: 'r',
        producedAt: '2026-06-03T00:00:00.000Z',
      },
      'first'
    );

    const second = await writeNodeArtifact(
      dir,
      {
        nodeId: 'review',
        outputType: 'findings',
        loopGroupPath: [{ groupId: 'a_b', iteration: 1 }],
        runId: 'r',
        producedAt: '2026-06-03T01:00:00.000Z',
      },
      'second'
    );

    expect(first.path).not.toBe(second.path);
    expect(await readFile(join(dir, first.path), 'utf8')).toBe('first');
    expect(await readFile(join(dir, second.path), 'utf8')).toBe('second');
    expect(await readNodeArtifacts(dir)).toHaveLength(2);
  });

  test('loop owner digests distinguish body node ids that sanitize alike', async () => {
    const [first, second] = await Promise.all([
      writeNodeArtifact(
        dir,
        {
          nodeId: 'a.b',
          outputType: 'findings',
          loopGroupPath: [{ groupId: 'group', iteration: 1 }],
          runId: 'r',
          producedAt: '2026-06-03T00:00:00.000Z',
        },
        'first'
      ),
      writeNodeArtifact(
        dir,
        {
          nodeId: 'a_b',
          outputType: 'findings',
          loopGroupPath: [{ groupId: 'group', iteration: 1 }],
          runId: 'r',
          producedAt: '2026-06-03T00:01:00.000Z',
        },
        'second'
      ),
    ]);

    expect(first.path).not.toBe(second.path);
    expect(await readFile(join(dir, first.path), 'utf8')).toBe('first');
    expect(await readFile(join(dir, second.path), 'utf8')).toBe('second');
    expect(new Set((await readNodeArtifacts(dir)).map(entry => entry.nodeId))).toEqual(
      new Set(['a.b', 'a_b'])
    );
  });

  test('loop owner namespace cannot alias valid top-level or delimiter-shaped loop ids', async () => {
    const topLevel = await writeNodeArtifact(
      dir,
      {
        nodeId: 'group-iteration-1__leaf',
        outputType: 'findings',
        runId: 'r',
        producedAt: '2026-06-03T00:00:00.000Z',
      },
      'top-level'
    );
    const loop = await writeNodeArtifact(
      dir,
      {
        nodeId: 'leaf',
        outputType: 'findings',
        loopGroupPath: [{ groupId: 'group', iteration: 1 }],
        runId: 'r',
        producedAt: '2026-06-03T00:01:00.000Z',
      },
      'loop'
    );
    const [nested, delimiterShaped] = await Promise.all([
      writeNodeArtifact(
        dir,
        {
          nodeId: 'leaf',
          outputType: 'findings',
          loopGroupPath: [
            { groupId: 'outer', iteration: 1 },
            { groupId: 'inner', iteration: 2 },
          ],
          runId: 'r',
          producedAt: '2026-06-03T00:02:00.000Z',
        },
        'nested'
      ),
      writeNodeArtifact(
        dir,
        {
          nodeId: 'inner-iteration-2__leaf',
          outputType: 'findings',
          loopGroupPath: [{ groupId: 'outer', iteration: 1 }],
          runId: 'r',
          producedAt: '2026-06-03T00:03:00.000Z',
        },
        'delimiter-shaped'
      ),
    ]);

    expect(new Set([topLevel.path, loop.path, nested.path, delimiterShaped.path]).size).toBe(4);
    expect(await readNodeArtifacts(dir)).toHaveLength(4);
  });

  test('readNodeArtifacts rejects invalid loop_group frame metadata', async () => {
    await writeNodeArtifact(
      dir,
      { nodeId: 'good', outputType: 'plan', runId: 'r', producedAt: '2026-06-03T00:00:00.000Z' },
      'ok'
    );
    await writeFile(
      join(dir, 'nodes', 'empty-loop.meta.json'),
      JSON.stringify({
        nodeId: 'empty-loop',
        outputType: 'plan',
        loopGroupPath: [],
        path: 'nodes/empty-loop.md',
        runId: 'r',
        producedAt: '2026-06-03T00:00:00.000Z',
        size: 1,
      }),
      'utf8'
    );
    await writeFile(
      join(dir, 'nodes', 'zero-iteration.meta.json'),
      JSON.stringify({
        nodeId: 'zero-iteration',
        outputType: 'plan',
        loopGroupPath: [{ groupId: 'group', iteration: 0 }],
        path: 'nodes/zero-iteration.md',
        runId: 'r',
        producedAt: '2026-06-03T00:00:00.000Z',
        size: 1,
      }),
      'utf8'
    );

    expect((await readNodeArtifacts(dir)).map(entry => entry.nodeId)).toEqual(['good']);
  });

  test('writeNodeArtifact rejects invalid loop_group frames before creating sidecars', async () => {
    await expect(
      writeNodeArtifact(
        dir,
        {
          nodeId: 'empty-path',
          outputType: 'plan',
          loopGroupPath: [],
          runId: 'r',
          producedAt: '2026-06-03T00:00:00.000Z',
        },
        'invalid'
      )
    ).rejects.toThrow();
    await expect(
      writeNodeArtifact(
        dir,
        {
          nodeId: 'zero-iteration',
          outputType: 'plan',
          loopGroupPath: [{ groupId: 'group', iteration: 0 }],
          runId: 'r',
          producedAt: '2026-06-03T00:00:00.000Z',
        },
        'invalid'
      )
    ).rejects.toThrow();

    expect(await readdir(dir)).toEqual([]);
  });

  test('re-writing the SAME node id (e.g. on resume) overwrites without a collision error', async () => {
    await writeNodeArtifact(
      dir,
      { nodeId: 'planner', outputType: 'plan', runId: 'r', producedAt: '2026-06-03T00:00:00.000Z' },
      'v1'
    );
    await writeNodeArtifact(
      dir,
      { nodeId: 'planner', outputType: 'plan', runId: 'r', producedAt: '2026-06-03T01:00:00.000Z' },
      'v2'
    );
    expect(await readFile(join(dir, 'nodes', 'planner.md'), 'utf8')).toBe('v2');
  });

  test('re-writing the same loop owner uses value equality and keeps one current artifact', async () => {
    const first = await writeNodeArtifact(
      dir,
      {
        nodeId: 'review',
        outputType: 'findings',
        loopGroupPath: [{ groupId: 'group', iteration: 2 }],
        runId: 'r',
        producedAt: '2026-06-03T00:00:00.000Z',
      },
      'v1'
    );
    const second = await writeNodeArtifact(
      dir,
      {
        nodeId: 'review',
        outputType: 'findings',
        loopGroupPath: [{ groupId: 'group', iteration: 2 }],
        runId: 'r',
        producedAt: '2026-06-03T01:00:00.000Z',
      },
      'v2'
    );

    expect(second.path).toBe(first.path);
    expect(await readFile(join(dir, first.path), 'utf8')).toBe('v2');
    expect(await readNodeArtifacts(dir)).toEqual([second]);
  });

  test('non-ENOENT prior-owner read failures reject without replacing output', async () => {
    await writeNodeArtifact(
      dir,
      { nodeId: 'a.b', outputType: 'plan', runId: 'r', producedAt: '2026-06-03T00:00:00.000Z' },
      'first'
    );
    const metaPath = join(dir, 'nodes', 'a_b.meta.json');
    await rm(metaPath);
    await mkdir(metaPath);

    await expect(
      writeNodeArtifact(
        dir,
        { nodeId: 'a_b', outputType: 'plan', runId: 'r', producedAt: '2026-06-03T01:00:00.000Z' },
        'second'
      )
    ).rejects.toThrow();
    expect(await readFile(join(dir, 'nodes', 'a_b.md'), 'utf8')).toBe('first');
  });

  test('readNodeArtifacts skips schema-invalid meta files (valid JSON, wrong shape)', async () => {
    await writeNodeArtifact(
      dir,
      { nodeId: 'good', outputType: 'plan', runId: 'r', producedAt: '2026-06-03T00:00:00.000Z' },
      'ok'
    );
    // Parseable JSON but missing required fields → safeParse fails → skipped, not fatal.
    await writeFile(join(dir, 'nodes', 'wrong.meta.json'), JSON.stringify({ foo: 'bar' }), 'utf8');

    const entries = await readNodeArtifacts(dir);
    expect(entries.map(e => e.nodeId)).toEqual(['good']);
  });
});
