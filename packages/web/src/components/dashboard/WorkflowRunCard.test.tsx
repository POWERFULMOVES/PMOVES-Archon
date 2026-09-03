import { describe, expect, test } from 'bun:test';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router';
import type { DashboardRunResponse } from '@/lib/api';
import { useWorkflowStore } from '@/stores/workflow-store';
import { WorkflowRunCard } from './WorkflowRunCard';

const parallelRun: DashboardRunResponse = {
  id: 'run-parallel',
  workflow_name: 'implement',
  conversation_id: 'conv-1',
  parent_conversation_id: null,
  codebase_id: 'codebase-1',
  status: 'running',
  outcome: null,
  user_message: 'Implement the change',
  metadata: {},
  started_at: '2026-09-01T10:00:00.000Z',
  completed_at: null,
  last_activity_at: '2026-09-01T10:01:00.000Z',
  working_path: '/workspace/archon',
  user_id: null,
  parent_run_id: null,
  adopted_from_run_id: null,
  output_root: null,
  codebase_name: 'Archon',
  platform_type: 'cli',
  worker_platform_id: null,
  parent_platform_id: null,
  active_nodes: ['parallel-a', 'parallel-b'],
  current_step_name: null,
  total_steps: null,
  current_step_status: null,
  agents_completed: null,
  agents_failed: null,
  agents_total: null,
};

describe('WorkflowRunCard', () => {
  test('renders every active node from the initial dashboard response', () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <WorkflowRunCard run={parallelRun} onCancel={() => undefined} />
      </MemoryRouter>
    );

    expect(html).toContain('Active nodes:');
    expect(html).toContain('parallel-a, parallel-b');
  });

  test('does not fall back to stale REST nodes after live lifecycle events finish them', () => {
    const serverWorkflows = useWorkflowStore.getInitialState().workflows;
    serverWorkflows.set(parallelRun.id, {
      runId: parallelRun.id,
      workflowName: parallelRun.workflow_name,
      status: 'running',
      activeNodeIds: [],
      dagNodes: [
        { nodeId: 'parallel-a', name: 'parallel-a', status: 'completed' },
        { nodeId: 'parallel-b', name: 'parallel-b', status: 'failed' },
      ],
      artifacts: [],
      startedAt: Date.now(),
      currentTool: null,
    });

    try {
      const html = renderToStaticMarkup(
        <MemoryRouter>
          <WorkflowRunCard run={parallelRun} onCancel={() => undefined} />
        </MemoryRouter>
      );

      expect(html).not.toContain('Active node');
      expect(html).not.toContain('parallel-a, parallel-b');
    } finally {
      serverWorkflows.delete(parallelRun.id);
    }
  });

  test('treats a null wait from the runtime boundary as absent', () => {
    const pausedApprovalRun = {
      ...parallelRun,
      status: 'paused',
      metadata: {
        wait: null,
        approval: { message: 'Approve the result?' },
      },
    } as unknown as DashboardRunResponse;

    const html = renderToStaticMarkup(
      <MemoryRouter>
        <WorkflowRunCard
          run={pausedApprovalRun}
          onCancel={() => undefined}
          onApprove={() => undefined}
        />
      </MemoryRouter>
    );

    expect(html).toContain('Approve the result?');
    expect(html).toContain('Approve</button>');
  });
});
