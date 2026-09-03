import { describe, expect, test } from 'bun:test';
import {
  isNodeContextMode,
  nodeContextForMode,
  resolveNodeContextMode,
  resumeSourceNodeId,
} from './node-context';

describe('workflow node context inspector state', () => {
  test('round-trips inherit, fresh, shared, and resume modes', () => {
    expect(resolveNodeContextMode(undefined)).toBe('inherit');
    expect(resolveNodeContextMode('fresh')).toBe('fresh');
    expect(resolveNodeContextMode('shared')).toBe('shared');
    expect(resolveNodeContextMode({ resume: 'scope' })).toBe('resume');

    expect(nodeContextForMode('inherit', 'fresh')).toBeUndefined();
    expect(nodeContextForMode('fresh', undefined)).toBe('fresh');
    expect(nodeContextForMode('shared', undefined)).toBe('shared');
    expect(nodeContextForMode('resume', { resume: 'scope' })).toEqual({ resume: 'scope' });
  });

  test('starts a new resume selector empty and exposes its edited source ID', () => {
    const context = nodeContextForMode('resume', 'fresh');
    expect(context).toEqual({ resume: '' });
    expect(resumeSourceNodeId({ resume: 'review-scope' })).toBe('review-scope');
  });

  test('accepts only inspector context modes', () => {
    expect(isNodeContextMode('resume')).toBe(true);
    expect(isNodeContextMode('unexpected')).toBe(false);
  });
});
