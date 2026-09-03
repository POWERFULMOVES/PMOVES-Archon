import type { Workflow } from '../primitives/workflow';

/**
 * Source rank for the "other" group: project first, then global, then bundled,
 * then any unrecognised source at the end (#2578). The fallback covers the
 * widened `Workflow['source']` (`WorkflowSource | (string & {})`) without
 * indexing a literal-keyed map with a `string` and getting `undefined`.
 */
function sourceRank(source: Workflow['source']): number {
  switch (source) {
    case 'project':
      return 0;
    case 'global':
      return 1;
    case 'bundled':
      return 2;
    default:
      return 3;
  }
}

/** Source rank for the "other" group: project first, then global, then bundled. */
function bySourceThenName(a: Workflow, b: Workflow): number {
  return sourceRank(a.source) - sourceRank(b.source) || a.name.localeCompare(b.name);
}

/**
 * Order workflows for the run picker (PR #1929).
 *
 * Repo-curated recommended names lead, in their declared (config) order and
 * filtered to names that actually resolved to a workflow. Duplicate names are
 * collapsed to their first occurrence so a repeated entry never pins the same
 * workflow twice (duplicate picker rows / React key collision). The rest
 * follow, sorted project → global → bundled then alphabetically. The returned
 * `recommended` list lets the picker draw the group divider.
 */
export function orderWithRecommended(
  workflows: Workflow[],
  recommendedNames: string[]
): { ordered: Workflow[]; recommended: Workflow[] } {
  const uniqueRecommendedNames = [...new Set(recommendedNames)];
  const recommendedSet = new Set(uniqueRecommendedNames);
  const recommended = uniqueRecommendedNames
    .map(name => workflows.find(w => w.name === name))
    .filter((w): w is Workflow => w !== undefined);
  const rest = workflows.filter(w => !recommendedSet.has(w.name)).sort(bySourceThenName);
  return { ordered: [...recommended, ...rest], recommended };
}
