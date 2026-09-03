/**
 * Guards the refresh-on-expiry contract of the OAuth mint path.
 *
 * pi-ai 0.84 dropped the SDK's `getOAuthApiKey` helper, so Archon now owns
 * the expiry decision (`oauth.ts`). The contract is subtle enough to have
 * regressed once already: `toAuth` (behind `getApiKey`) derives request auth
 * from whatever credential it is given and never throws on a stale token, so
 * refresh MUST be decided by comparing `expires` against the clock — an
 * error-triggered refresh never fires, and a stale subscription token would
 * be silently delivered to runs.
 */
import { describe, expect, mock, test } from 'bun:test';

import { mintOAuthApiKey, type OAuthCredentials, type OAuthProviderInterface } from './oauth';

function makeCreds(expires: number): OAuthCredentials {
  return { type: 'oauth', access: 'stored-access', refresh: 'stored-refresh', expires };
}

function makeProvider(overrides?: Partial<OAuthProviderInterface>): {
  provider: OAuthProviderInterface;
  refreshToken: ReturnType<typeof mock>;
  getApiKey: ReturnType<typeof mock>;
} {
  const refreshToken = mock(
    async (): Promise<OAuthCredentials> => ({
      type: 'oauth',
      access: 'refreshed-access',
      refresh: 'refreshed-refresh',
      expires: Date.now() + 3_600_000,
    })
  );
  const getApiKey = mock(async (creds: OAuthCredentials) => ({ apiKey: creds.access }));
  const provider: OAuthProviderInterface = {
    id: 'fake',
    login: async () => {
      throw new Error('not under test');
    },
    refreshToken,
    getApiKey,
    ...overrides,
  };
  return { provider, refreshToken, getApiKey };
}

describe('mintOAuthApiKey', () => {
  test('unexpired credential mints without refreshing and echoes the input blob', async () => {
    const { provider, refreshToken } = makeProvider();
    const creds = makeCreds(Date.now() + 3_600_000);

    const result = await mintOAuthApiKey(provider, creds);

    expect(refreshToken).not.toHaveBeenCalled();
    expect(result.apiKey).toBe('stored-access');
    // Echoing the input lets the key-store's field comparison see "not
    // rotated" and skip the resave.
    expect(result.newCredentials).toBe(creds);
  });

  test('expired credential refreshes BEFORE minting and returns the rotated blob', async () => {
    const { provider, refreshToken, getApiKey } = makeProvider();
    const creds = makeCreds(Date.now() - 1000);

    const result = await mintOAuthApiKey(provider, creds);

    expect(refreshToken).toHaveBeenCalledTimes(1);
    // The mint must run on the REFRESHED credential, not the stale one.
    expect(getApiKey).toHaveBeenCalledWith(expect.objectContaining({ access: 'refreshed-access' }));
    expect(result.apiKey).toBe('refreshed-access');
    expect(result.newCredentials.access).toBe('refreshed-access');
  });

  test('refresh failure propagates so the caller can log oauth_refresh_failed', async () => {
    const { provider } = makeProvider({
      refreshToken: async () => {
        throw new Error('invalid_grant');
      },
    });
    const creds = makeCreds(Date.now() - 1000);

    await expect(mintOAuthApiKey(provider, creds)).rejects.toThrow('invalid_grant');
  });
});
