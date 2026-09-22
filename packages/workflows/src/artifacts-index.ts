import { createHash } from 'node:crypto';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { createLogger } from '@archon/paths';
import {
  nodeArtifactSchema,
  type NodeArtifact,
  type NodeArtifactLoopFrame,
} from './schemas/node-artifact';

/** Lazy logger (deferred so test mocks can intercept createLogger). */
let cachedLog: ReturnType<typeof createLogger> | undefined;
function getLog(): ReturnType<typeof createLogger> {
  if (!cachedLog) cachedLog = createLogger('artifacts-index');
  return cachedLog;
}

/** Subdirectory under the artifacts dir holding per-node typed outputs + metadata. */
const NODES_SUBDIR = 'nodes';
const nodeArtifactOwnerSchema = nodeArtifactSchema.pick({ nodeId: true, loopGroupPath: true });
const nodeArtifactWriteParamsSchema = nodeArtifactSchema.omit({ path: true, size: true });

type ArtifactOwner = Pick<NodeArtifact, 'nodeId' | 'loopGroupPath'>;

/**
 * Restrict a node id to a single safe path segment for use in a filename.
 * Node ids are normally simple identifiers; this guards against a stray
 * separator or `..` escaping the nodes directory.
 */
function safeSegment(id: string): string {
  return id.replace(/[^a-zA-Z0-9_-]/g, '_');
}

/** Build the single filename segment that identifies one typed node execution. */
function artifactStem(owner: ArtifactOwner): string {
  const nodeSegment = safeSegment(owner.nodeId);
  if (owner.loopGroupPath === undefined) return nodeSegment;

  // The dot makes loop stems disjoint from top-level safeSegment() output. Hash
  // the canonical original owner so valid ids containing our display separators
  // cannot alias one another; readable provenance remains in the metadata.
  const canonicalOwner = [
    owner.nodeId,
    owner.loopGroupPath.map(frame => [frame.groupId, frame.iteration]),
  ];
  const digest = createHash('sha256').update(JSON.stringify(canonicalOwner)).digest('hex');
  return `loop.${digest}__${nodeSegment}`;
}

function sameLoopGroupPath(
  left: NodeArtifactLoopFrame[] | undefined,
  right: NodeArtifactLoopFrame[] | undefined
): boolean {
  if (left === undefined || right === undefined) return left === right;
  return (
    left.length === right.length &&
    left.every(
      (frame, index) =>
        frame.groupId === right[index]?.groupId && frame.iteration === right[index]?.iteration
    )
  );
}

function sameArtifactOwner(left: ArtifactOwner, right: ArtifactOwner): boolean {
  return left.nodeId === right.nodeId && sameLoopGroupPath(left.loopGroupPath, right.loopGroupPath);
}

/**
 * Read the owner recorded in an existing `.meta.json`, or `undefined` if the
 * file is missing or corrupt. Used only by the collision guard in
 * `writeNodeArtifact`. Real filesystem failures remain visible to the caller.
 */
async function readArtifactOwner(metaPath: string): Promise<ArtifactOwner | undefined> {
  let rawMetadata: string;
  try {
    rawMetadata = await readFile(metaPath, 'utf8');
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === 'ENOENT') return undefined;
    throw err;
  }

  try {
    const parsed = nodeArtifactOwnerSchema.safeParse(JSON.parse(rawMetadata));
    return parsed.success ? parsed.data : undefined;
  } catch {
    return undefined;
  }
}

/**
 * Write a node's typed output artifact: the output text and metadata under
 * `nodes/`. Top-level nodes retain `nodes/<id>.md` + `<id>.meta.json`; a
 * loop_group body execution qualifies that identity with a stable digest of its
 * structured owner and records the readable ordered frames in metadata.
 * Per-execution files (no shared index): the index is derived on read by globbing,
 * so separate nodes, iterations, and runs never overwrite one another's metadata.
 * Concurrent writers are isolated by their identity-derived paths.
 *
 * Returns the written metadata. Throws on fs failure or a sanitized-id collision
 * — callers persist artifacts best-effort and must wrap this in their own
 * try/catch so an artifact write never fails an otherwise-successful node.
 */
export async function writeNodeArtifact(
  artifactsDir: string,
  params: Omit<NodeArtifact, 'path' | 'size'>,
  outputText: string
): Promise<NodeArtifact> {
  // Zod refinements such as positive iteration and non-empty lineage are not
  // represented in the inferred TypeScript primitives, so enforce them at the
  // durable constructor before creating either sidecar.
  const parsedParams = nodeArtifactWriteParamsSchema.parse(params);
  const nodesDir = join(artifactsDir, NODES_SUBDIR);
  await mkdir(nodesDir, { recursive: true });
  const owner: ArtifactOwner = {
    nodeId: parsedParams.nodeId,
    ...(parsedParams.loopGroupPath !== undefined
      ? { loopGroupPath: parsedParams.loopGroupPath }
      : {}),
  };
  const stem = artifactStem(owner);
  const metaPath = join(nodesDir, `${stem}.meta.json`);

  // Collision guard: top-level safeSegment() can collapse distinct node ids (for
  // example `a.b` and `a_b`), and loop digests retain an ownership check rather
  // than assuming their hash alone is authoritative. Compare the complete
  // producer identity and fail loudly instead of overwriting another artifact.
  const priorOwner = await readArtifactOwner(metaPath);
  if (priorOwner !== undefined && !sameArtifactOwner(priorOwner, owner)) {
    throw new Error(
      `node artifact id collision: distinct producers both map to filename segment '${stem}'`
    );
  }

  const relPath = join(NODES_SUBDIR, `${stem}.md`);
  await writeFile(join(artifactsDir, relPath), outputText, 'utf8');
  const meta: NodeArtifact = {
    nodeId: parsedParams.nodeId,
    outputType: parsedParams.outputType,
    ...(parsedParams.loopGroupPath !== undefined
      ? { loopGroupPath: parsedParams.loopGroupPath }
      : {}),
    path: relPath,
    runId: parsedParams.runId,
    producedAt: parsedParams.producedAt,
    size: Buffer.byteLength(outputText, 'utf8'),
    ...(parsedParams.sessionId !== undefined ? { sessionId: parsedParams.sessionId } : {}),
  };
  await writeFile(metaPath, JSON.stringify(meta, null, 2), 'utf8');
  return meta;
}

/**
 * Read all typed-artifact metadata entries from an artifacts dir by globbing
 * the per-node `.meta.json` files (the index is derived on read, never a single
 * shared file). A missing dir yields `[]` (no artifacts yet — not an error);
 * an unreadable/corrupt entry is skipped with a warning, not fatal.
 */
export async function readNodeArtifacts(artifactsDir: string): Promise<NodeArtifact[]> {
  const nodesDir = join(artifactsDir, NODES_SUBDIR);
  let files: string[];
  try {
    files = await readdir(nodesDir);
  } catch (err) {
    // ENOENT = the nodes dir was never created → no artifacts yet, not an error.
    // Any other fault (EACCES/ENOTDIR/EIO) must NOT masquerade as "empty" — a
    // permissions/disk problem should surface, not silently yield no artifacts.
    if ((err as NodeJS.ErrnoException).code === 'ENOENT') return [];
    getLog().warn({ nodesDir, err: err as Error }, 'artifacts.nodes_dir_read_failed');
    throw err;
  }
  const out: NodeArtifact[] = [];
  for (const file of files) {
    if (!file.endsWith('.meta.json')) continue;
    const full = join(nodesDir, file);
    try {
      const parsed = nodeArtifactSchema.safeParse(JSON.parse(await readFile(full, 'utf8')));
      if (parsed.success) {
        out.push(parsed.data);
      } else {
        getLog().warn({ file: full, issues: parsed.error.issues }, 'artifacts.index_entry_invalid');
      }
    } catch (err) {
      getLog().warn({ file: full, err: err as Error }, 'artifacts.index_entry_read_failed');
    }
  }
  return out;
}

/**
 * Return the most-recently-produced artifact of a given `output_type`, or
 * `undefined` if none exists. `producedAt` is a schema-validated ISO-8601 UTC
 * datetime, so the values sort lexicographically.
 */
export async function latestNodeArtifactOfType(
  artifactsDir: string,
  outputType: string
): Promise<NodeArtifact | undefined> {
  const matching = (await readNodeArtifacts(artifactsDir)).filter(e => e.outputType === outputType);
  let latest: NodeArtifact | undefined;
  for (const entry of matching) {
    if (latest === undefined || entry.producedAt > latest.producedAt) {
      latest = entry;
    }
  }
  return latest;
}
