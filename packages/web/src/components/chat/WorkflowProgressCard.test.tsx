import { describe, expect, mock, test } from 'bun:test';
import { Children, isValidElement, type ReactElement, type ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { AttentionWaitControls } from './WorkflowProgressCard';

function nodeText(node: ReactNode): string {
  if (typeof node === 'string' || typeof node === 'number') return String(node);
  if (!isValidElement(node)) return '';
  const props = node.props as { children?: ReactNode };
  return Children.toArray(props.children).map(nodeText).join('');
}

function findButton(node: ReactNode, label: string): ReactElement<{ onClick?: () => void }> | null {
  if (!isValidElement(node)) return null;
  const element = node as ReactElement<{ children?: ReactNode; onClick?: () => void }>;
  if (element.type === 'button' && nodeText(element).includes(label)) return element;
  for (const child of Children.toArray(element.props.children)) {
    const match = findButton(child, label);
    if (match) return match;
  }
  return null;
}

describe('WorkflowProgressCard action-required controls', () => {
  test('shows Resume and Abandon and sends the run ID through Resume', () => {
    const onResume = mock((_runId: string): void => undefined);
    const props = {
      runId: 'attention-run-1',
      workflowName: 'archon-deliver',
      message: 'Re-run the Windows check, then resume this run.',
      busy: false,
      onResume,
      onAbandon: mock((_runId: string): void => undefined),
    };

    const html = renderToStaticMarkup(<AttentionWaitControls {...props} />);
    expect(html).toContain(props.message);
    expect(html).toContain('Resume</button>');
    expect(html).toContain('Abandon</button>');
    expect(html).not.toContain('Approve</button>');
    expect(html).not.toContain('Reject</button>');

    const resume = findButton(AttentionWaitControls(props), 'Resume');
    expect(resume).not.toBeNull();
    resume?.props.onClick?.();
    expect(onResume).toHaveBeenCalledWith('attention-run-1');
  });
});
