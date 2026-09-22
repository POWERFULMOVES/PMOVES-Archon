import type { components } from '@/lib/api.generated';

/**
 * Where a workflow lives — engine-known (`project` / `global` / `bundled`).
 * Derived from the generated OpenAPI schema (`@/lib/api.generated`) so the
 * union cannot silently drift between this primitive and the server. #2578
 * closed a hand-maintained mirror here that collapsed unrecognised values to
 * `'bundled'`; the precedent is the same fix PR #2570 made for `CommandGroup`
 * (`packages/web/src/lib/command-groups.ts`). The console's lint guard
 * disallows named imports from `@/lib/api`, so the type is sourced from the
 * generated file directly (the `packages/web/src/lib/api.ts` re-export
 * carries the same bytes either way).
 */
export type WorkflowSource = components['schemas']['WorkflowSource'];

/**
 * One entry of a workflow's declared `inputs:` signature (#2470), flattened for
 * rendering. A run supplies values for these; an omitted name takes `default`, and a
 * `required` one with no value is refused before the run starts (#2554).
 */
export interface WorkflowInput {
  name: string;
  required: boolean;
  default: string | null;
  description: string | null;
}

export interface Workflow {
  name: string;
  description: string | null;
  /**
   * Where the workflow came from. Known values carry `WorkflowSource` literals
   * so the downstream helpers (`isReadOnlySource`, `saveTargetFor`) keep their
   * type-narrowed callers; the `(string & {})` widening surfaces an
   * unrecognised value verbatim rather than collapsing it to `'bundled'`,
   * which would silently mark it read-only and turn Save into Save-as
   * (#2578). The `& {}` keeps the known literals visible in autocomplete.
   */
  source: WorkflowSource | (string & {});
  /**
   * Keys this workflow's YAML declares that the engine silently drops (#2213).
   * Empty for a clean workflow. The workflow still loads and runs — this is what
   * was ignored, which can include a gate the author believed they had.
   */
  parseWarnings: string[];
  /** Declared `inputs:` in declaration order; empty when the workflow declares none. */
  inputs: WorkflowInput[];
}

/**
 * The workflow object as `GET /api/workflows` sends it, for the fields the console
 * reads. Exported because `skills/workflows.ts` describes the same wire shape for its
 * own `listWorkflows`/`getWorkflowGraph` calls — two hand-rolled copies drifted once
 * already (its copy never learned about `inputs`, which type-checked silently because
 * a missing optional property still satisfies the parameter type, and would have gone
 * on compiling while the run form quietly stopped rendering).
 */
export interface RawWorkflowShape {
  name: string;
  description?: string | null;
  inputs?: Record<
    string,
    { required?: boolean; default?: string; description?: string } | null | undefined
  >;
  returns?: string;
}

interface RawWorkflowEntry {
  workflow: RawWorkflowShape;
  source: string;
  parseWarnings?: string[];
}

export function toWorkflow(raw: RawWorkflowEntry): Workflow {
  // Pass the raw source through verbatim. Three distinct sources matter for
  // sort + badge — project (repo-local) > global (home-scoped
  // `~/.archon/workflows`) > bundled (defaults shipped with Archon) — but
  // an unrecognised value must not be collapsed to `'bundled'` (that would
  // mark it read-only and turn Save into Save-as, #2578). Mirrors
  // `groupCommandsBySource` in `@/lib/command-groups.ts` (#2570): surface
  // unknown values rather than hide them.
  const src: WorkflowSource | (string & {}) = raw.source;
  // Object key order preserves the YAML's declaration order for string keys, so the
  // run form renders inputs in the order the author wrote them.
  const inputs: WorkflowInput[] = Object.entries(raw.workflow.inputs ?? {}).map(([name, spec]) => ({
    name,
    required: spec?.required === true,
    default: spec?.default ?? null,
    description: spec?.description ?? null,
  }));
  return {
    name: raw.workflow.name,
    description: raw.workflow.description ?? null,
    source: src,
    parseWarnings: raw.parseWarnings ?? [],
    inputs,
  };
}
