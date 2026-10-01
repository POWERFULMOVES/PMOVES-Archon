import { describe, test, expect } from 'bun:test';

import { repositoryPath } from './api';

describe('repositoryPath', () => {
  test('reads owner and repo, dropping surrounding slashes and .git', () => {
    expect(repositoryPath('owner/repo')).toEqual({ owner: 'owner', repo: 'repo' });
    expect(repositoryPath('/owner/repo.git')).toEqual({ owner: 'owner', repo: 'repo' });
    expect(repositoryPath('///owner/repo///')).toEqual({ owner: 'owner', repo: 'repo' });
  });

  test('rejects paths that are not exactly owner/repo', () => {
    expect(repositoryPath('')).toBeNull();
    expect(repositoryPath('////')).toBeNull();
    expect(repositoryPath('owner')).toBeNull();
    expect(repositoryPath('owner//repo')).toBeNull();
    expect(repositoryPath('owner/repo/extra')).toBeNull();
    expect(repositoryPath('owner/..')).toBeNull();
  });

  // The previous /^\/+|\/+$/g trim was quadratic in a run of slashes
  // (CodeQL js/polynomial-redos): 200k slashes measured 11.6s that way on bun 1.4.2.
  test('stays linear on a long run of slashes', () => {
    const slashes = '/'.repeat(200_000);
    const started = performance.now();
    expect(repositoryPath(`owner${slashes}x`)).toBeNull();
    expect(repositoryPath(`${slashes}owner/repo${slashes}`)).toEqual({
      owner: 'owner',
      repo: 'repo',
    });
    expect(performance.now() - started).toBeLessThan(1000);
  });
});
