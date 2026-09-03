import type { DagNode } from '@/lib/api';

export type NodeContextMode = 'inherit' | 'fresh' | 'shared' | 'resume';
type NodeContext = NonNullable<DagNode['context']>;

export function resolveNodeContextMode(context: DagNode['context']): NodeContextMode {
  if (context === 'fresh' || context === 'shared') return context;
  if (typeof context === 'object') return 'resume';
  return 'inherit';
}

export function nodeContextForMode(
  mode: NodeContextMode,
  current: DagNode['context']
): NodeContext | undefined {
  if (mode === 'inherit') return undefined;
  if (mode === 'fresh' || mode === 'shared') return mode;
  return typeof current === 'object' ? current : { resume: '' };
}

export function resumeSourceNodeId(context: DagNode['context']): string {
  return typeof context === 'object' ? context.resume : '';
}

export function isNodeContextMode(value: string): value is NodeContextMode {
  return value === 'inherit' || value === 'fresh' || value === 'shared' || value === 'resume';
}
