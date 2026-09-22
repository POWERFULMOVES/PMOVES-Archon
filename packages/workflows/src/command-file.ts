import type { DagNode, IncludeDirective } from './schemas';
import { isAgentNode, isIncludeDirective, isLoopGroupNode, isLoopNode } from './schemas';

/** Return the command-file name used by a node, including deferred loop prompts. */
export function getFileBackedCommandName(node: DagNode): string | undefined {
  if (isAgentNode(node) && node.source.kind === 'command') return node.source.name;
  if (isLoopNode(node) && typeof node.loop.command === 'string') return node.loop.command;
  return undefined;
}

/** Collect command-file names from a node list, including nested loop-group bodies. */
export function collectFileBackedCommandNames(
  nodes: readonly (DagNode | IncludeDirective)[]
): Set<string> {
  const names = new Set<string>();
  const visit = (node: DagNode | IncludeDirective): void => {
    if (isIncludeDirective(node)) return;
    const commandName = getFileBackedCommandName(node);
    if (commandName !== undefined) names.add(commandName);
    if (isLoopGroupNode(node)) {
      for (const child of node.loop_group.nodes) visit(child);
    }
  };
  for (const node of nodes) visit(node);
  return names;
}
