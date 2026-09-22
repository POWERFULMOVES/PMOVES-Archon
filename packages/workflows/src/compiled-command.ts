import type { BindingDirective, TriggerRule } from './schemas';
import type { JsonValue } from './output-ref';

/** Engine-private per-node metadata attached during load-time include expansion.
 * Symbols survive object spreads but stay out of YAML, JSON, API payloads, and
 * persisted workflow definitions.
 *
 * A symbol does NOT ride `structuredClone`, so every payload declared here has to be
 * re-attached by `cloneNodeForInclude` (include-expander.ts) and re-walked by BOTH
 * rewrite passes (`rewriteNodeOutputRefs`, `applyInputsMacro`). A payload that misses
 * any of the three works at one nesting level and silently vanishes at two. */
export const COMPILED_LOOP_COMMAND = Symbol('archon.compiled-loop-command');

export type CompiledLoopCommand =
  | { prompt: string; error?: never }
  | { prompt?: never; error: string };

export interface LoopWithCompiledCommand {
  [COMPILED_LOOP_COMMAND]?: CompiledLoopCommand;
}

/**
 * The node-local `with:` map a command node carried before include expansion compiled
 * its body into an inline prompt (#2964).
 *
 * Composition materializes a command node so the block's refs can be namespaced and its
 * declared inputs bound, which leaves `with:` — a field the schema admits only on the
 * `command` source variant, so an author cannot write it on a prompt node (#2478) —
 * with nowhere to live on the result. Dropping it silently unbound every name the node
 * supplied itself: the compiled body's `$INPUTS.<name>` reached the model as a literal
 * token, or as an empty string when a decoy input had been declared to get past the
 * missing-input check. The executor and the dry-run simulator resolve this payload for a
 * materialized node exactly as they resolve `source.with` for an unmaterialized one, so
 * a binding means the same thing standalone and composed.
 */
export const COMPOSED_BINDINGS = Symbol('archon.composed-bindings');

export type ComposedBindings = Record<string, JsonValue | BindingDirective>;

export interface NodeWithComposedBindings {
  [COMPOSED_BINDINGS]?: ComposedBindings;
}

/** Read a node's surviving node-local bindings. One accessor, so the cast lives in one place. */
export function readComposedBindings(node: object): ComposedBindings | undefined {
  return (node as NodeWithComposedBindings)[COMPOSED_BINDINGS];
}

/** Attach the bindings a materialized command node must keep. @see COMPOSED_BINDINGS */
export function attachComposedBindings(node: object, bindings: ComposedBindings): void {
  (node as NodeWithComposedBindings)[COMPOSED_BINDINGS] = bindings;
}

/** @see ComposedNodeMeta */
export const COMPOSED_NODE = Symbol('archon.composed-node');

/**
 * The caller-level predicate that decides whether one include instance is active.
 * Every descendant carries a copy because load-time expansion removes the include node.
 */
interface ComposedBlockBoundaryBase {
  dependsOn: string[];
  entryTriggerRules: [TriggerRule, ...TriggerRule[]];
  when?: string;
}

export type ComposedBlockBoundary = ComposedBlockBoundaryBase &
  (
    | {
        /** The node's own trigger/when fields normally enforce this boundary at the entry. */
        isEntry: true;
        /** Resume needs this entry's rule rather than the block-wide rule set. */
        entryTriggerRule: TriggerRule;
      }
    | {
        isEntry: false;
        entryTriggerRule?: never;
      }
  );

/**
 * Per-node record of the workflow a node was AUTHORED in, attached when that
 * workflow is inlined into a parent (#1764). It is what lets a composed node keep
 * behaving like its own file's node instead of the composing parent's:
 *
 *  - `origin` — the authoring workflow's name. Write-once (innermost wins), so a
 *    node nested three files deep still names the file that declared it.
 *  - `inputs` — that workflow's contract-resolved `inputs:` (defaults applied),
 *    delivered to its `bash:`/`script:` nodes as `INPUTS_<UPPER_SNAKE>` env vars.
 *    Write-once for the same reason, and because input names carry no namespace:
 *    two levels both declaring `plan` have no disambiguator, so the inner one wins.
 *  - `blockEntry` — this node starts its block. The executor clears the sequential
 *    session cursor there so a composed workflow begins as coldly as it would
 *    standalone.
 *  - `boundaries` — caller-level activation predicates for enclosing include instances,
 *    outermost first. Non-entry descendants enforce them before their local trigger rule.
 */
export interface ComposedNodeMeta {
  origin: string;
  inputs?: Record<string, JsonValue>;
  blockEntry?: true;
  boundaries?: ComposedBlockBoundary[];
}

export interface NodeWithComposedMeta {
  [COMPOSED_NODE]?: ComposedNodeMeta;
}

/** Read a node's composition record. One accessor, so the symbol cast lives in one place. */
export function readComposedMeta(node: object): ComposedNodeMeta | undefined {
  return (node as NodeWithComposedMeta)[COMPOSED_NODE];
}

export interface IncludeCommandReadError {
  path: string;
  message: string;
  operation: 'inspect' | 'read';
}

export type IncludeCommandContent = string | null | IncludeCommandReadError;

export function isIncludeCommandReadError(
  value: IncludeCommandContent | undefined
): value is IncludeCommandReadError {
  return typeof value === 'object' && value !== null;
}
