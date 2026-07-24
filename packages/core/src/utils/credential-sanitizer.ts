/**
 * Credential Sanitizer
 * Removes sensitive values from strings to prevent credential leaks
 */

const SENSITIVE_ENV_VARS = ['GH_TOKEN', 'GITHUB_TOKEN'];

function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function sanitizeCredentials(input: string): string {
  let result = input;

  for (const envVar of SENSITIVE_ENV_VARS) {
    const value = process.env[envVar];
    if (value && value.length > 0) {
      result = result.replace(new RegExp(escapeRegExp(value), 'g'), '[REDACTED]');
    }
  }

  // Catch any URL-embedded credentials we might have missed. The userinfo
  // segment is length-bounded (1–256) so this cannot degrade to polynomial
  // backtracking on hostile input — real GitHub PAT/user:pass combos are far
  // shorter, so redaction coverage is unchanged. (CodeQL js/polynomial-redos)
  result = result.replace(/https:\/\/[^@\s]{1,256}@github\.com/g, 'https://[REDACTED]@github.com');

  return result;
}

export function sanitizeError(error: Error): Error {
  const sanitized = new Error(sanitizeCredentials(error.message));
  if (error.stack) {
    sanitized.stack = sanitizeCredentials(error.stack);
  }
  return sanitized;
}
