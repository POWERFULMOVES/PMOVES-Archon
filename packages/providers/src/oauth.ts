/**
 * SDK-boundary wrapper around Pi's OAuth utilities (`@earendil-works/pi-ai`).
 *
 * The Pi SDK dependency lives only in `@archon/providers`, so the rest of
 * Archon (the credential store + the subscription-connect bridge in
 * `@archon/core`) drives OAuth THROUGH this module instead of importing the
 * SDK directly. Pi 0.84.0 reorganized its public surface — the
 * `getOAuthProvider`/`getOAuthApiKey`/`OAuthProviderInterface` exports that
 * `@archon/core` calls were dropped from the SDK. This module now owns those
 * shapes locally and adapts the new `OAuthAuth` singletons (anthropic, github
 * copilot) to the legacy callback-driven interface the bridge and key-store
 * still speak. The legacy `openaiCodexOAuthProvider` export is intentionally
 * absent — see the `getOAuthProvider` note below.
 *
 * Why this serves more than Pi: Pi's OAuth flows authenticate against the
 * native runtimes' OWN OAuth apps (the Claude Code app, the GitHub Copilot
 * device flow), so the token Pi mints is exactly what the native
 * Claude/Copilot providers already accept. One subscription connect therefore
 * powers the native runtimes, not just Pi — the delivery map
 * (`@archon/core/credentials/delivery`) routes the resolved credential to
 * whichever provider consumes it.
 */

import type {
  OAuthAuth,
  OAuthCredential,
  ProviderAuthInteraction,
  AuthPrompt,
  AuthEvent,
} from '@earendil-works/pi-ai';

/* ─── Lazy loader for the SDK's OAuth singletons ──────────────────────────── */

/**
 * The SDK ships `anthropicOAuth` and `githubCopilotOAuth` as deep subpath
 * modules (`@earendil-works/pi-ai/dist/auth/oauth/*`) that are NOT in the
 * package's `exports` field (the public `./oauth` subpath is type-only as of
 * 0.84.2, and `./bun-oauth` only registers loaders for compiled binaries), so
 * a static ESM import fails with "Cannot find module" — Bun enforces the
 * exports gate the same way Node.js does. We resolve the SDK package root via
 * its public `package.json` (the one subpath that IS in `exports`), then load
 * the deep file through `createRequire` — the filesystem path bypasses the
 * resolver's exports gate. Loaded lazily and cached so the OAuth flow modules
 * are only touched when a login/refresh/mint actually happens.
 */
const oauthAuthCache = new Map<string, OAuthAuth>();

async function loadOAuthAuth(moduleFile: string, exportName: string): Promise<OAuthAuth> {
  const cached = oauthAuthCache.get(moduleFile);
  if (cached) return cached;
  const { createRequire } = await import('node:module');
  const { fileURLToPath } = await import('node:url');
  // Called through the module object: node:path types dirname/join as
  // PlatformPath methods, so destructuring them trips eslint unbound-method.
  const path = await import('node:path');
  // fileURLToPath returns backslash-separated paths on Windows — build the
  // deep path with node:path, never string concatenation on '/'.
  const sdkPkgPath = fileURLToPath(import.meta.resolve('@earendil-works/pi-ai/package.json'));
  const deepPath = path.join(path.dirname(sdkPkgPath), 'dist', 'auth', 'oauth', moduleFile);
  const require = createRequire(import.meta.url);
  const mod = require(deepPath) as Record<string, OAuthAuth>;
  const oauthAuth = mod[exportName];
  if (!oauthAuth) {
    throw new Error(`Pi SDK module '${moduleFile}' has no export '${exportName}'.`);
  }
  oauthAuthCache.set(moduleFile, oauthAuth);
  return oauthAuth;
}

/* ─── Legacy surface preserved for `@archon/core` consumers ───────────────── */

/** Subset of the pre-0.84 callback-driven login surface the bridge relies on. */
export interface OAuthLoginCallbacks {
  onAuth(info: { url: string; instructions?: string }): void;
  onDeviceCode(info: { userCode: string; verificationUri: string }): void;
  onManualCodeInput?(): Promise<string>;
  onPrompt(prompt: unknown): Promise<string>;
  onSelect(prompt: {
    options: readonly { id: string; label?: string }[];
  }): Promise<string | undefined>;
  onProgress?(message: string): void;
  signal?: AbortSignal;
}

/** Legacy `OAuthCredentials` re-export (pi-ai ships an identical shape). */
export type OAuthCredentials = OAuthCredential;

/** Legacy `OAuthAuthInfo` / `OAuthDeviceCodeInfo` — preserved for callers. */
export interface OAuthAuthInfo {
  url: string;
  instructions?: string;
}
export interface OAuthDeviceCodeInfo {
  userCode: string;
  verificationUri: string;
}

/**
 * Pre-0.84 OAuth provider singleton shape: an `id` for the key-store path,
 * an opt-in `usesCallbackServer` flag (Anthropic + the now-Archon-owned
 * OpenAI Codex bind a local fixed-port callback server during login; the
 * bridge uses this flag to supersede colliding in-flight logins), and the
 * `login` / `refreshToken` / `getApiKey` methods.
 */
export interface OAuthProviderInterface {
  readonly id: string;
  readonly usesCallbackServer?: boolean;
  login(callbacks: OAuthLoginCallbacks): Promise<OAuthCredential>;
  refreshToken(
    credentials: OAuthCredential,
    options?: { signal?: AbortSignal }
  ): Promise<OAuthCredential>;
  getApiKey(credentials: OAuthCredential): Promise<{ apiKey: string }>;
}

/* ─── Adapter: `OAuthAuth` (pi-ai ≥ 0.84) → legacy callback-driven surface ── */

/** Map the SDK's `interaction` prompts/events onto the legacy callbacks. */
function adaptLoginCallbacks(
  oauthAuth: OAuthAuth,
  callbacks: OAuthLoginCallbacks
): ProviderAuthInteraction {
  return {
    signal: callbacks.signal ?? new AbortController().signal,
    prompt: async (prompt: AuthPrompt): Promise<string> => {
      if (prompt.type === 'manual_code') {
        if (!callbacks.onManualCodeInput) {
          throw new Error(
            `OAuth provider '${oauthAuth.name}' requested a manual code but no onManualCodeInput callback was supplied.`
          );
        }
        return callbacks.onManualCodeInput();
      }
      if (prompt.type === 'select') {
        return (await callbacks.onSelect({ options: prompt.options })) ?? '';
      }
      // text / secret — Pi uses these for one-off prompts (e.g. github-copilot
      // enterprise domain). The caller decides how to answer; the Archon
      // bridge has no interactive channel and returns "" (blank default).
      return callbacks.onPrompt(prompt);
    },
    notify: (event: AuthEvent): void => {
      if (event.type === 'auth_url') {
        callbacks.onAuth({ url: event.url, instructions: event.instructions });
        return;
      }
      if (event.type === 'device_code') {
        callbacks.onDeviceCode({
          userCode: event.userCode,
          verificationUri: event.verificationUri,
        });
        return;
      }
      if (event.type === 'progress' || event.type === 'info') {
        callbacks.onProgress?.(event.message);
      }
    },
  };
}

/**
 * Wrap a pi-ai 0.84 `OAuthAuth` singleton in the legacy
 * `OAuthProviderInterface` shape. The `id` is caller-supplied because pi-ai's
 * `OAuthAuth` doesn't carry an Archon-style vendor id (only a human-readable
 * display name).
 */
function adaptOAuthAuth(
  id: string,
  loader: () => Promise<OAuthAuth>,
  usesCallbackServer: boolean
): OAuthProviderInterface {
  return {
    id,
    usesCallbackServer,
    async login(callbacks): Promise<OAuthCredential> {
      const oauthAuth = await loader();
      return oauthAuth.login(adaptLoginCallbacks(oauthAuth, callbacks));
    },
    async refreshToken(credentials, options): Promise<OAuthCredential> {
      const oauthAuth = await loader();
      const signal = options?.signal ?? new AbortController().signal;
      return oauthAuth.refresh(credentials, signal);
    },
    async getApiKey(credentials): Promise<{ apiKey: string }> {
      const oauthAuth = await loader();
      // toAuth is a side-effect-free derivation ({ apiKey?, headers?, baseUrl? })
      // from whatever credential it is given — it does NOT check expiry.
      const auth = await oauthAuth.toAuth(credentials);
      if (!auth.apiKey) {
        throw new Error(
          `Pi OAuth provider '${oauthAuth.name}' produced no apiKey for the stored credential.`
        );
      }
      return { apiKey: auth.apiKey };
    },
  };
}

export const anthropicOAuthProvider: OAuthProviderInterface = adaptOAuthAuth(
  'anthropic',
  () => loadOAuthAuth('anthropic.js', 'anthropicOAuth'),
  true
);
export const githubCopilotOAuthProvider: OAuthProviderInterface = adaptOAuthAuth(
  'github-copilot',
  () => loadOAuthAuth('github-copilot.js', 'githubCopilotOAuth'),
  false
);

/**
 * Returns the `OAuthProviderInterface` for the given vendor id, or undefined
 * if the vendor is API-key only or its flow is Archon-owned (the
 * `openai`/ChatGPT Codex flow runs through `@archon/core`'s PKCE module —
 * see `credentials/openai-oauth.ts`; it would drop the `id_token` the Codex
 * CLI requires, #1924, so it is deliberately NOT exposed here).
 */
export function getOAuthProvider(id: string): OAuthProviderInterface | undefined {
  switch (id) {
    case 'anthropic':
      return anthropicOAuthProvider;
    case 'github-copilot':
      return githubCopilotOAuthProvider;
    default:
      return undefined;
  }
}

/* ─── Auto-refresh + mint: the key-store calls `getOAuthApiKey(...)` ───────── */

/**
 * Mint a usable bearer from a stored OAuth blob; auto-refresh on expiry.
 *
 * Mirrors the pre-0.84 `getOAuthApiKey` contract that
 * `@archon/core/db/user-provider-key-store.ts` consumes:
 *   - input: `{ [providerId]: creds }` — the key-store destructures by id to
 *     stay vendor-agnostic (`piProvider.id` is the key it uses)
 *   - output: `{ newCredentials, apiKey }`, where `newCredentials` echoes the
 *     input unless the refresh path rotated the blob (the caller detects
 *     rotation by field comparison and re-saves); `null` if no provider backs
 *     this vendor or no credential was supplied
 *
 * The expiry check is OURS, exactly as it was in the pre-0.84 SDK helper:
 * `toAuth` derives request auth from whatever credential it is given and
 * never throws on a stale token, so refresh MUST be decided by comparing
 * `expires` against the clock before minting — an error-triggered refresh
 * would never fire. Throws on refresh failure (HTTP 401, invalid_grant,
 * etc.) so the caller can record `user_provider_key.oauth_refresh_failed`.
 */
export async function getOAuthApiKey(
  providerId: string,
  options: Record<string, OAuthCredential> & { signal?: AbortSignal }
): Promise<{ newCredentials: OAuthCredential; apiKey: string } | null> {
  const provider = getOAuthProvider(providerId);
  if (!provider) return null;
  const creds: OAuthCredential | undefined = options[providerId];
  if (!creds) return null;
  return mintOAuthApiKey(provider, creds, options.signal);
}

/**
 * The refresh-then-mint core of `getOAuthApiKey`, split out at the
 * provider-object seam so the expiry decision is testable without loading
 * the real SDK flows (whose `refreshToken` performs a live network call).
 */
export async function mintOAuthApiKey(
  provider: OAuthProviderInterface,
  credentials: OAuthCredential,
  signal?: AbortSignal
): Promise<{ newCredentials: OAuthCredential; apiKey: string }> {
  let creds = credentials;
  if (Date.now() >= creds.expires) {
    // Refreshers return a brand-new credential (the refresh token rotates on
    // the server side); the caller saves it via `saveUserProviderKey(...)` so
    // the next read doesn't re-refresh.
    creds = await provider.refreshToken(creds, { signal });
  }
  const minted = await provider.getApiKey(creds);
  return { newCredentials: creds, apiKey: minted.apiKey };
}
