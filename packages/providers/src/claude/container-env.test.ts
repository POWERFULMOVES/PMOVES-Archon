import { describe, test, expect, beforeEach, afterEach } from 'bun:test';
import { buildRequestSubprocessEnv } from './provider';

/**
 * Env-isolation enforcement point: a container run must receive ONLY the
 * Archon-managed env bag over a minimal base — host `process.env` must NEVER
 * cross into the container. A host run keeps inheriting the host env unchanged.
 */
describe('buildRequestSubprocessEnv — container env isolation', () => {
  const CANARY = 'ARCHON_HOST_CANARY_SECRET';

  beforeEach(() => {
    process.env[CANARY] = 'leaked-host-secret';
  });
  afterEach(() => {
    delete process.env[CANARY];
  });

  test('container run EXCLUDES host process.env (canary absent), keeps managed creds', () => {
    const env = buildRequestSubprocessEnv({
      execContext: { kind: 'container', containerId: 'c1' },
      env: { ANTHROPIC_API_KEY: 'sk-managed', CODEBASE_VAR: 'x' },
    });
    expect(env[CANARY]).toBeUndefined(); // host secret did NOT cross the boundary
    expect(env.ANTHROPIC_API_KEY).toBe('sk-managed'); // managed creds delivered
    expect(env.CODEBASE_VAR).toBe('x');
    expect(env.TERM).toBe('dumb'); // minimal base only
  });

  test('host run INHERITS host process.env (canary present) — unchanged behavior', () => {
    const env = buildRequestSubprocessEnv({ env: { FOO: 'bar' } });
    expect(env[CANARY]).toBe('leaked-host-secret');
    expect(env.FOO).toBe('bar');
  });

  test('container run mirrors CLAUDE_API_KEY -> ANTHROPIC_API_KEY', () => {
    const env = buildRequestSubprocessEnv({
      execContext: { kind: 'container', containerId: 'c1' },
      env: { CLAUDE_API_KEY: 'sk-claude' },
    });
    expect(env.ANTHROPIC_API_KEY).toBe('sk-claude');
    expect(env[CANARY]).toBeUndefined();
  });
});

/**
 * Auth precedence. The Claude CLI prefers ANTHROPIC_API_KEY over
 * CLAUDE_CODE_OAUTH_TOKEN, so a key sitting in the host environment silently
 * outranks a subscription token that was deliberately provided for the run —
 * rebilling it, or failing it outright when that key has no credit.
 *
 * Verified against Claude Code 2.1.209:
 *   key + token -> "Credit balance is too low"  (the key wins)
 *   token alone -> "401 Invalid bearer token"   (the token is used)
 */
describe('buildRequestSubprocessEnv — inherited ANTHROPIC_API_KEY vs OAuth token', () => {
  const KEY = 'ANTHROPIC_API_KEY';
  const TOKEN = 'CLAUDE_CODE_OAUTH_TOKEN';
  const saved: Record<string, string | undefined> = {};

  beforeEach(() => {
    saved[KEY] = process.env[KEY];
    saved[TOKEN] = process.env[TOKEN];
  });
  afterEach(() => {
    for (const k of [KEY, TOKEN]) {
      if (saved[k] === undefined) delete process.env[k];
      else process.env[k] = saved[k];
    }
  });

  test('drops an INHERITED api key when an OAuth token is present', () => {
    process.env[KEY] = 'sk-ant-inherited-dead-key';
    process.env[TOKEN] = 'sk-ant-oat01-subscription';
    const env = buildRequestSubprocessEnv(undefined);
    expect(env.ANTHROPIC_API_KEY).toBeUndefined();
    expect(env.CLAUDE_CODE_OAUTH_TOKEN).toBe('sk-ant-oat01-subscription');
  });

  test('KEEPS an inherited api key when there is no OAuth token', () => {
    process.env[KEY] = 'sk-ant-only-credential';
    delete process.env[TOKEN];
    const env = buildRequestSubprocessEnv(undefined);
    // The key is the ONLY credential here — dropping it would break api-key installs.
    expect(env.ANTHROPIC_API_KEY).toBe('sk-ant-only-credential');
  });

  test('KEEPS an EXPLICIT managed api key even alongside an OAuth token', () => {
    process.env[TOKEN] = 'sk-ant-oat01-subscription';
    const env = buildRequestSubprocessEnv({ env: { ANTHROPIC_API_KEY: 'sk-managed' } });
    // Archon-managed per-user credential: an explicit delivery, not inheritance.
    expect(env.ANTHROPIC_API_KEY).toBe('sk-managed');
  });

  test('respects an EXPLICIT empty string as a deliberate decision', () => {
    process.env[KEY] = 'sk-ant-inherited';
    process.env[TOKEN] = 'sk-ant-oat01-subscription';
    const env = buildRequestSubprocessEnv({ env: { ANTHROPIC_API_KEY: '' } });
    // hasOwnProperty, not truthiness — the caller said '' and we do not second-guess it.
    expect(env.ANTHROPIC_API_KEY).toBe('');
  });

  test('container run is unaffected — host env never crossed the boundary anyway', () => {
    process.env[KEY] = 'sk-ant-inherited';
    const env = buildRequestSubprocessEnv({
      execContext: { kind: 'container', containerId: 'c1' },
      env: { ANTHROPIC_API_KEY: 'sk-managed', CLAUDE_CODE_OAUTH_TOKEN: 'sk-ant-oat01' },
    });
    expect(env.ANTHROPIC_API_KEY).toBe('sk-managed');
  });
});
