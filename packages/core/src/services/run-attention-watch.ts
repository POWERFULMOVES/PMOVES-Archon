/**
 * Wait until one run needs someone.
 *
 * The run ROW is the authority: every wake re-reads `remote_agent_workflow_runs` and
 * asks `runAttention` what it says. The Postgres `NOTIFY` channel is only a doorbell —
 * it makes the answer arrive sooner, it is never the answer. That split is forced by
 * evidence: `resolveAndCancelApprovalGate` writes a terminal `cancelled` while
 * inserting only an `approval_received` row, a `child_workflow` pause persists no
 * event at all, and `approval_requested` is written fire-and-forget. An event-derived
 * wake would miss all three.
 *
 * Core owns the capability; a host owns the interval, the deadline, and the lifecycle
 * (the `listDueWorkflowContinuations` / `workflow-resume-service` division). This
 * function performs NO writes: it reads run rows and returns a value.
 */
import { getDbNotificationListener } from '../db/connection';
import { WORKFLOW_EVENT_NOTIFY_CHANNEL } from '../db/adapters/types';
import * as workflowDb from '../db/workflows';
import { runAttention } from '@archon/workflows/schemas/workflow-run';
import type {
  RunAttention,
  WorkflowRun,
  WorkflowRunStatus,
} from '@archon/workflows/schemas/workflow-run';
import { createLogger } from '@archon/paths';

// Lazy logger — NEVER at module scope
let cachedLog: ReturnType<typeof createLogger> | undefined;
function getLog(): ReturnType<typeof createLogger> {
  if (!cachedLog) cachedLog = createLogger('run-attention');
  return cachedLog;
}

/**
 * The same cadence on BOTH dialects, deliberately. The dashboard poller relaxes to
 * 10s when a notification listener is present; that is safe for it because every
 * transition it tracks inserts an event. Two transitions this waiter must catch do
 * not: `approval_requested` is written fire-and-forget before the awaited pause
 * (dag-executor.ts), and a `child_workflow` pause writes no event by design. So
 * NOTIFY is a latency win for the transitions that ring it, never the reason this is
 * correct. A single-run row read is cheap enough to make that the default.
 */
export const DEFAULT_ATTENTION_POLL_INTERVAL_MS = 1000;

/**
 * Safety bound on the sub-run chain walk. Same number and rationale as
 * `MAX_CASCADE_RUNS` in `operations/workflow-operations.ts` (a corrupted run tree must
 * not walk forever); kept separate because that walk cancels a subtree and this one
 * only reads. Exceeding it is reported, never assumed away.
 */
const MAX_CHAIN_RUNS = 500;

/**
 * Why the wait returned — deliberately a different type from `RunAttention`.
 * `RunAttention` is what a host consumes; this is why THIS wait ended. A caller has to
 * destructure `kind` before it can reach a status, so a deadline can never be misread
 * as a terminal run status. That is the failure mode this shape exists to prevent.
 */
export type RunWaitResult =
  | { kind: 'attention'; attention: RunAttention }
  | { kind: 'deadline'; runId: string; observedStatus: WorkflowRunStatus }
  | { kind: 'aborted'; runId: string }
  | { kind: 'not_found'; runId: string };

export interface RunAttentionWaitOptions {
  /** Stop waiting when this aborts. The run row is left untouched. */
  signal?: AbortSignal;
  /** Give up after this long. Omitted means wait until the run says something. */
  deadlineMs?: number;
  /** Backstop re-read cadence. Defaults to `DEFAULT_ATTENTION_POLL_INTERVAL_MS`. */
  pollIntervalMs?: number;
  /**
   * Called once, with the status the opening read saw, when that read finds nothing
   * to report and the wait settles in to watch. It does not fire when the run already
   * has something to say, because then nothing was ever waited for.
   *
   * This is the moment the wait becomes live, and it is the only moment a caller
   * cannot infer: a run that goes terminal after it produces a WAKE, while the same
   * transition before it would have been an ordinary durable read of a settled row.
   *
   * Awaited, so a host that has to deliver this somewhere can report a failed
   * delivery instead of dropping it. A rejection ends the wait.
   */
  onAttached?: (observedStatus: WorkflowRunStatus) => void | Promise<void>;
}

/** What woke a re-read. Logged at debug so a slow wake is diagnosable. */
type WakeSource = 'immediate' | 'notify' | 'interval' | 'deadline';

function unreadable(
  runId: string,
  reason: 'child_run_missing' | 'child_chain_too_deep',
  detail: string
): RunAttention {
  return { kind: 'unreadable', runId, reason, detail };
}

/**
 * Resolve `blocked_on_child` by walking the chain, which the pure projection cannot do.
 *
 * A parent pauses blocked on a child whether that child sits on its own gate or is
 * merely still running, and the parent row cannot tell those apart. So the walk asks
 * the child directly:
 *  - the child needs a response → return that, addressed at the CHILD and its node. This
 *    is the case a parent-row-only rule gets wrong in the dangerous direction: nothing
 *    moves until someone decides.
 *  - the child is terminal → return null and keep waiting. The parent's auto-resume
 *    hook (`maybeResumeParentRun`) should re-enter it. That hook is in-process and
 *    opportunistic, so a dropped re-entry leaves the parent paused — but a waiter
 *    cannot tell "resume in flight" from "resume dropped", and guessing is exactly
 *    what this design refuses to do.
 *  - the child is running, pending, or on a scheduled `wait:` → null. Normal progress.
 *    An action-required wait is returned as attention by the same projection above.
 */
async function resolveAttention(run: WorkflowRun): Promise<RunAttention | null> {
  let attention = runAttention(run);
  let steps = 0;
  while (attention?.kind === 'blocked_on_child') {
    steps += 1;
    if (steps > MAX_CHAIN_RUNS) {
      return unreadable(
        attention.runId,
        'child_chain_too_deep',
        `sub-run chain is deeper than ${String(MAX_CHAIN_RUNS)} runs`
      );
    }
    const child = await workflowDb.getWorkflowRun(attention.childRunId);
    if (!child) {
      return unreadable(
        attention.runId,
        'child_run_missing',
        `blocked on sub-run ${attention.childRunId}, which has no row`
      );
    }
    const childAttention = runAttention(child);
    // A terminal child, like a still-working one, means nobody is needed YET.
    if (childAttention === null || childAttention.kind === 'terminal') return null;
    attention = childAttention;
  }
  return attention;
}

/**
 * Subscribe to the run's doorbell when the dialect has one. Returns null on SQLite,
 * where the interval is the only wake source. A listener that drops is logged and not
 * replaced: the interval backstop already covers it, and failing the wait over a lost
 * optimization would be worse than waking a second later.
 */
async function subscribeToRunDoorbell(
  runId: string,
  onDoorbell: () => void
): Promise<(() => void) | null> {
  const listener = getDbNotificationListener();
  if (!listener) return null;
  try {
    return await listener.listen(
      WORKFLOW_EVENT_NOTIFY_CHANNEL,
      payload => {
        if (payload === runId) onDoorbell();
      },
      err => {
        getLog().debug({ err, runId }, 'run_attention.doorbell_dropped');
      }
    );
  } catch (err) {
    getLog().debug({ err, runId }, 'run_attention.doorbell_unavailable');
    return null;
  }
}

/**
 * Block until `runId` reaches a state it will not leave without someone acting, or
 * until the deadline or abort signal ends the wait.
 *
 * Durable, not live-only: the first thing this does is read the row, so a host that
 * attaches after the transition gets the same answer as one that attached before it.
 */
export async function waitForRunAttention(
  runId: string,
  opts: RunAttentionWaitOptions = {}
): Promise<RunWaitResult> {
  const pollIntervalMs = opts.pollIntervalMs ?? DEFAULT_ATTENTION_POLL_INTERVAL_MS;
  const deadlineAt = opts.deadlineMs === undefined ? undefined : Date.now() + opts.deadlineMs;
  const signal = opts.signal;

  if (signal?.aborted) return { kind: 'aborted', runId };

  // A doorbell can ring between iterations, while nothing is waiting on it.
  let pendingDoorbell = false;
  let wake: ((source: WakeSource) => void) | null = null;
  const unsubscribe = await subscribeToRunDoorbell(runId, () => {
    if (wake) wake('notify');
    else pendingDoorbell = true;
  });

  const nextWake = (): Promise<WakeSource> => {
    if (pendingDoorbell) {
      pendingDoorbell = false;
      return Promise.resolve('notify');
    }
    return new Promise<WakeSource>(resolve => {
      const timers: ReturnType<typeof setTimeout>[] = [];
      function finish(source: WakeSource): void {
        if (wake === null) return;
        wake = null;
        for (const timer of timers) clearTimeout(timer);
        signal?.removeEventListener('abort', onAbort);
        resolve(source);
      }
      function onAbort(): void {
        // The loop re-reads and then sees the aborted signal; no separate source.
        finish('interval');
      }
      wake = finish;
      timers.push(
        setTimeout(() => {
          finish('interval');
        }, pollIntervalMs)
      );
      if (deadlineAt !== undefined) {
        timers.push(
          setTimeout(
            () => {
              finish('deadline');
            },
            Math.max(0, deadlineAt - Date.now())
          )
        );
      }
      signal?.addEventListener('abort', onAbort, { once: true });
    });
  };

  try {
    let wakeSource: WakeSource = 'immediate';
    let attached = false;
    for (;;) {
      const run = await workflowDb.getWorkflowRun(runId);
      if (!run) return { kind: 'not_found', runId };

      const attention = await resolveAttention(run);
      if (attention) {
        getLog().debug({ runId, wakeSource, attention: attention.kind }, 'run_attention.resolved');
        return { kind: 'attention', attention };
      }
      // Checked AFTER the read so a transition landing on the deadline still wins.
      if (signal?.aborted) return { kind: 'aborted', runId };
      if (deadlineAt !== undefined && Date.now() >= deadlineAt) {
        return { kind: 'deadline', runId, observedStatus: run.status };
      }
      if (!attached) {
        attached = true;
        await opts.onAttached?.(run.status);
      }
      wakeSource = await nextWake();
    }
  } finally {
    // `nextWake` clears its own timer and abort listener before it resolves, and the
    // loop only returns between awaits, so the subscription is all that is left.
    unsubscribe?.();
  }
}
