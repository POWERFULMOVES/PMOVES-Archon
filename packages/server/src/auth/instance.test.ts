import { afterEach, beforeEach, describe, expect, mock, test } from 'bun:test';

interface SignupUser {
  email?: string;
  name?: string;
}

interface AuthOptions {
  database: unknown;
  secret: string;
  baseURL?: string;
  trustedOrigins?: string[];
  emailAndPassword: { enabled: boolean; disableSignUp: boolean };
  user: { modelName: string };
  session: { modelName: string };
  account: { modelName: string };
  verification: { modelName: string };
  databaseHooks: {
    user: {
      create: {
        before: (user: SignupUser) => Promise<{ data: SignupUser }>;
      };
    };
  };
}

interface FakeAuth {
  handler: () => Response;
  api: Record<string, never>;
}

interface FakeLogger {
  info: () => void;
  error: () => void;
}

let capturedOptions: AuthOptions | undefined;
let poolOptions: { connectionString: string; max: number } | undefined;
const endPool = mock(async (): Promise<void> => undefined);

class FakePool {
  constructor(options: { connectionString: string; max: number }) {
    poolOptions = options;
  }

  end = endPool;
}

class FakeAPIError extends Error {
  readonly status: string;

  constructor(status: string, options: { message: string }) {
    super(options.message);
    this.status = status;
  }
}

mock.module('better-auth', (): { betterAuth: (options: AuthOptions) => FakeAuth } => ({
  betterAuth: (options: AuthOptions): FakeAuth => {
    capturedOptions = options;
    return { handler: mock((): Response => new Response()), api: {} };
  },
}));

mock.module('better-auth/api', (): { APIError: typeof FakeAPIError } => ({
  APIError: FakeAPIError,
}));
mock.module('pg', (): { Pool: typeof FakePool } => ({ Pool: FakePool }));
mock.module('@archon/paths', (): { createLogger: () => FakeLogger } => ({
  createLogger: (): FakeLogger => ({
    info: mock((): undefined => undefined),
    error: mock((): undefined => undefined),
  }),
}));

const { closeAuth, getAuth, resetAuthForTest } = await import('./instance');

const DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/archon';
const SECRET = 'a-secure-better-auth-secret-with-32-characters';

function enabledEnv(overrides: NodeJS.ProcessEnv = {}): NodeJS.ProcessEnv {
  return {
    DATABASE_URL,
    BETTER_AUTH_SECRET: SECRET,
    ARCHON_AUTH_OPEN_SIGNUP: 'true',
    ...overrides,
  };
}

function signupHook(): AuthOptions['databaseHooks']['user']['create']['before'] {
  const hook = capturedOptions?.databaseHooks.user.create.before;
  if (!hook) throw new Error('Better Auth signup hook was not configured');
  return hook;
}

beforeEach((): void => {
  capturedOptions = undefined;
  poolOptions = undefined;
  endPool.mockClear();
  resetAuthForTest();
});

afterEach(async (): Promise<void> => {
  await closeAuth();
  resetAuthForTest();
});

describe('getAuth', (): void => {
  test('returns null without both PostgreSQL and a signing secret', (): void => {
    expect(getAuth({})).toBeNull();
    expect(capturedOptions).toBeUndefined();
    expect(poolOptions).toBeUndefined();
  });

  test('constructs the configured PostgreSQL email/password instance', (): void => {
    const auth = getAuth(
      enabledEnv({
        BETTER_AUTH_URL: 'https://archon.example.test',
        BETTER_AUTH_TRUSTED_ORIGINS: 'https://one.example.test, https://two.example.test',
      })
    );

    expect(auth).not.toBeNull();
    expect(poolOptions).toEqual({ connectionString: DATABASE_URL, max: 5 });
    expect(capturedOptions).toMatchObject({
      secret: SECRET,
      baseURL: 'https://archon.example.test',
      trustedOrigins: ['https://one.example.test', 'https://two.example.test'],
      emailAndPassword: { enabled: true, disableSignUp: false },
      user: { modelName: 'remote_agent_auth_user' },
      session: { modelName: 'remote_agent_auth_session' },
      account: { modelName: 'remote_agent_auth_account' },
      verification: { modelName: 'remote_agent_auth_verification' },
    });
  });
});

describe('signup hook', (): void => {
  test('rejects signup when the safe default disables it', async (): Promise<void> => {
    getAuth(enabledEnv({ ARCHON_AUTH_OPEN_SIGNUP: undefined }));
    expect(capturedOptions?.emailAndPassword.disableSignUp).toBe(true);
    await expect(signupHook()({ email: 'person@example.test' })).rejects.toThrow(
      'Signup is disabled.'
    );
  });

  test('rejects missing and non-allowlisted email addresses', async (): Promise<void> => {
    getAuth(
      enabledEnv({
        ARCHON_AUTH_OPEN_SIGNUP: undefined,
        ARCHON_AUTH_ALLOWED_EMAILS: 'allowed@example.test',
      })
    );

    await expect(signupHook()({ name: 'Missing Email' })).rejects.toMatchObject({
      message: 'Email is required.',
      status: 'BAD_REQUEST',
    });
    await expect(signupHook()({ email: 'other@example.test' })).rejects.toThrow(
      'This email is not on the invite allowlist.'
    );
  });

  test('returns the original user for allowlisted and open signup', async (): Promise<void> => {
    const allowlisted = { email: 'allowed@example.test', name: 'Allowed' };
    getAuth(
      enabledEnv({
        ARCHON_AUTH_OPEN_SIGNUP: undefined,
        ARCHON_AUTH_ALLOWED_EMAILS: 'allowed@example.test',
      })
    );
    await expect(signupHook()(allowlisted)).resolves.toEqual({ data: allowlisted });

    await closeAuth();
    resetAuthForTest();
    capturedOptions = undefined;
    const open = { email: 'anyone@example.test', name: 'Anyone' };
    getAuth(enabledEnv());
    await expect(signupHook()(open)).resolves.toEqual({ data: open });
  });
});
