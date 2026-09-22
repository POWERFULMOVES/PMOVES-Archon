import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { afterEach, expect, test } from 'bun:test';

import {
  getOrCreateReloadedExtensionLoader,
  resetReloadedExtensionLoaderCache,
} from './resource-loader';

const originalAgentDir = process.env.PI_CODING_AGENT_DIR;
let scratchDir: string | undefined;

afterEach(() => {
  resetReloadedExtensionLoaderCache();
  if (originalAgentDir === undefined) {
    delete process.env.PI_CODING_AGENT_DIR;
  } else {
    process.env.PI_CODING_AGENT_DIR = originalAgentDir;
  }
  if (scratchDir) {
    rmSync(scratchDir, { recursive: true, force: true });
    scratchDir = undefined;
  }
});

test("loads native guidance and only the workflow node's declared skill", async () => {
  scratchDir = mkdtempSync(join(tmpdir(), 'archon-pi-context-'));
  const agentDir = join(scratchDir, 'agent');
  const projectRoot = join(scratchDir, 'project');
  const cwd = join(projectRoot, 'nested');
  const globalContextPath = join(agentDir, 'AGENTS.md');
  const projectContextPath = join(projectRoot, 'CLAUDE.md');
  const ambientSkillPath = join(agentDir, 'skills', 'ambient-skill');
  const declaredSkillPath = join(scratchDir, 'declared-skill');

  mkdirSync(agentDir, { recursive: true });
  mkdirSync(cwd, { recursive: true });
  writeFileSync(globalContextPath, '# User rules\n');
  writeFileSync(projectContextPath, '# Project rules\n');
  mkdirSync(ambientSkillPath, { recursive: true });
  mkdirSync(declaredSkillPath, { recursive: true });
  writeFileSync(
    join(ambientSkillPath, 'SKILL.md'),
    '---\nname: ambient-skill\ndescription: must stay hidden\n---\n'
  );
  writeFileSync(
    join(declaredSkillPath, 'SKILL.md'),
    '---\nname: declared-skill\ndescription: selected by the node\n---\n'
  );
  process.env.PI_CODING_AGENT_DIR = agentDir;

  const { loader } = await getOrCreateReloadedExtensionLoader(cwd, {
    additionalSkillPaths: [declaredSkillPath],
  });

  expect(loader.getAgentsFiles().agentsFiles).toEqual(
    expect.arrayContaining([
      { path: globalContextPath, content: '# User rules\n' },
      { path: projectContextPath, content: '# Project rules\n' },
    ])
  );
  expect(loader.getSkills().skills.map(skill => skill.name)).toEqual(['declared-skill']);
});
