import { describe, it, expect } from 'bun:test';
import { formatDeprecationNotice } from './deprecation';
import type { WorkflowDefinition } from './schemas/workflow';

const deprecatedWorkflow = (overrides: Partial<WorkflowDefinition> = {}): WorkflowDefinition =>
  ({
    name: 'archon-fix-github-issue',
    description: 'test workflow',
    nodes: [{ id: 'n', prompt: 'p' }],
    deprecated: { message: 'Switch to the sdlc pack instead.' },
    ...overrides,
  }) as unknown as WorkflowDefinition;

describe('formatDeprecationNotice (#2781)', () => {
  it('returns undefined for a workflow without the marker', () => {
    expect(formatDeprecationNotice(deprecatedWorkflow({ deprecated: undefined }))).toBeUndefined();
  });

  it('composes the pinned run-start wording with the declared message', () => {
    // Every element of the maintainer's directive (#2781, comment 5395761250)
    // must be present verbatim in structure: removal announcement + the declared
    // replacement pointer + both keep/copy exits.
    expect(formatDeprecationNotice(deprecatedWorkflow())).toBe(
      '⚠️ `archon-fix-github-issue` is deprecated and will be removed in an upcoming release. ' +
        'Switch to the sdlc pack instead. ' +
        'To keep using this workflow after removal, copy the workflow file into your project ' +
        '`.archon/workflows/` or your global `~/.archon/workflows/`.'
    );
  });
});
