/**
 * Resolve the directory a chat/web run should read its workflow SOURCE from.
 *
 * A conversation's `cwd` is frequently a git worktree. Worktrees carry the tracked
 * `.archon` of whatever branch they are on, which is rarely the branch the author is
 * editing workflows on — so discovery from the worktree either missed a new workflow
 * entirely or resolved an older copy of one. The previous answer was to copy the
 * canonical repo's `.archon` into the worktree before discovering (`worktree-sync`),
 * which made the worktree's own tracked files dirty and dragged ignored content
 * (`.archon/.env`, cross-run `state/`) along with it.
 *
 * Reading from the canonical repo directly gets the same workflows without writing
 * anything into the worktree. The run then freezes what it found, so later edits do
 * not change a run already in flight.
 */
import { getCanonicalRepoPath, isWorktreePath } from '@archon/git';
import { createLogger } from '@archon/paths';

/** Lazy-initialized logger (deferred so test mocks can intercept createLogger) */
let cachedLog: ReturnType<typeof createLogger> | undefined;
function getLog(): ReturnType<typeof createLogger> {
  if (!cachedLog) cachedLog = createLogger('workflow-source-root');
  return cachedLog;
}

/**
 * The authoring root for `cwd`: its canonical repository when `cwd` is a worktree,
 * otherwise `undefined` (meaning "same as cwd" — every caller treats an absent value
 * as the pre-existing behavior).
 *
 * THROWS when git cannot answer. That is deliberate and the opposite of what this used to
 * do: swallowing the error returned `undefined`, which callers read as "the cwd IS the
 * authoring root" and then froze the worktree — the source/target confusion this exists to
 * prevent. Not knowing and guessing wrong are different outcomes, so the caller decides.
 */
export async function resolveWorkflowSourceRoot(cwd: string): Promise<string | undefined> {
  // A git failure is NOT the same as "this is not a worktree". Swallowing it returned
  // `undefined`, which callers read as "the cwd is the authoring root" — and then froze
  // the worktree, which is the very source/target confusion this exists to prevent. If we
  // cannot tell, say so and let the caller refuse to start.
  const isWorktree = await isWorktreePath(cwd).catch((error: Error) => {
    throw new Error(
      `Cannot determine whether ${cwd} is a worktree, so the run's authoring source is ` +
        `unknown: ${error.message}`
    );
  });
  if (!isWorktree) return undefined;
  const canonical = await getCanonicalRepoPath(cwd).catch((error: Error) => {
    throw new Error(
      `Cannot resolve the canonical repository for worktree ${cwd}, so the run's authoring ` +
        `source is unknown: ${error.message}`
    );
  });
  if (canonical === cwd) return undefined;
  getLog().debug({ cwd, canonical }, 'workflow.source_root_resolved_canonical');
  return canonical;
}
