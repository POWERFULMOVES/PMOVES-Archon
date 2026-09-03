import { describe, expect, test } from 'bun:test';
import type { WorkflowDefinition } from '@/lib/api';
import { serializeToYaml } from './YamlCodeView';

describe('serializeToYaml node context', () => {
  test('serializes a named resume selector as nested YAML', () => {
    const definition: WorkflowDefinition = {
      name: 'addressable',
      description: 'Addressable session example',
      nodes: [
        { id: 'scope', prompt: 'Scope the work' },
        {
          id: 'synthesize',
          prompt: 'Synthesize',
          depends_on: ['scope'],
          context: { resume: 'scope' },
        },
      ],
    };

    const yaml = serializeToYaml(definition);
    expect(yaml).toContain('    context:\n      resume: scope');
    expect(yaml).not.toContain('[object Object]');
  });

  test('preserves scalar context forms', () => {
    const definition: WorkflowDefinition = {
      name: 'scalar-context',
      description: 'Scalar context example',
      nodes: [
        { id: 'fresh', prompt: 'Fresh', context: 'fresh' },
        { id: 'shared', prompt: 'Shared', context: 'shared' },
      ],
    };

    const yaml = serializeToYaml(definition);
    expect(yaml).toContain('    context: fresh');
    expect(yaml).toContain('    context: shared');
  });
});
