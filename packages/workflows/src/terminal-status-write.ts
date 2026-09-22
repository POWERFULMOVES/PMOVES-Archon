import { createLogger } from '@archon/paths';

/** Lazy-initialized logger (deferred so test mocks can intercept createLogger) */
let cachedLog: ReturnType<typeof createLogger> | undefined;
function getLog(): ReturnType<typeof createLogger> {
  if (!cachedLog) cachedLog = createLogger('workflow.terminal-status-write');
  return cachedLog;
}

/**
 * A run's terminal status (completed / failed / cancelled) could not be recorded.
 *
 * Recovery boundaries branch on this type to keep the run distinguishable from one
 * that merely failed: the process finished, but the row still says `running`, so no
 * ordinary outcome can be reported for it and no compensating write should be tried
 * over the same write channel.
 */
export class TerminalStatusWriteError extends Error {
  readonly cause: unknown;

  constructor(cause: unknown) {
    super(
      `Failed to persist terminal workflow status: ${
        cause instanceof Error ? cause.message : String(cause)
      }`
    );
    this.name = 'TerminalStatusWriteError';
    this.cause = cause;
  }
}

/** Identifies which terminal write failed, for the diagnostic log below. */
export interface TerminalStatusWriteContext {
  workflowRunId: string;
  /** Greppable call-site tag, e.g. `executor.backstop_fail_failed`. */
  site: string;
}

/**
 * Await a terminal run-status write and convert a rejection into the typed marker.
 *
 * Logs the original database error here so no call site has to remember to. `site`
 * carries what the per-call `.catch()` handlers this wrapper replaced used to carry:
 * which of the ~14 terminal writes is the one that failed.
 */
export async function requireTerminalStatusWrite<T>(
  write: Promise<T>,
  context: TerminalStatusWriteContext
): Promise<T> {
  try {
    return await write;
  } catch (error) {
    getLog().error(
      { err: error as Error, workflowRunId: context.workflowRunId, site: context.site },
      'workflow.terminal_status_write_failed'
    );
    throw new TerminalStatusWriteError(error);
  }
}
