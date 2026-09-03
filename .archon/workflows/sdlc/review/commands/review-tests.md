# Test Review — Regression Protection

Find one defect: **the change establishes or alters meaningful behavior, and no test would fail when that behavior regresses in a plausible way.** Tests protect outcomes and invariants — count, lines, and coverage percentages are not outcomes. Read-only: never modify files, commit, or post anywhere.

Read `$ARTIFACTS_DIR/review/scope.md` first, and the project's `architecture.md` if it has one. Anchor the review on the accepted work order's stated invariants, and scale depth to what the change can destroy: irreversible or destructive paths, lifecycle ownership, persisted contracts and schemas, credentials and auth boundaries, integration boundaries, and concurrency over shared state each get an explicit attempt to refute the invariant they rest on; a prose-only change gets the minimum. In light mode, verify prior findings from this lens first, then examine only the delta.

## A finding needs all four

1. **Behavior or invariant** — what the change promises and why it matters.
2. **Coverage map** — the existing tests (any level) that do and do not protect it; inspect **assertions, not test titles**.
3. **Plausible regression** — a realistic future edit that violates the behavior while every current test still passes.
4. **Smallest valuable test** — setup, action, observable assertion; it fails for that regression, passes for the intended implementation, and survives a behavior-preserving refactor.

Never report "missing test for line X" — name the observable failure that remains unprotected. Before reporting, falsify the gap: search for tests under other names, check whether types or schemas already make the regression impossible, and confirm the path is supported behavior.

## Prefer leverage

Prioritize gaps where regression means incorrect user-visible behavior, data loss, failure semantics becoming success, or resume/concurrency/ordering breaks. Test at the lowest stable boundary that proves the behavior — and only at the unit level when it can prove it without mocking the behavior under review away. Check the existing doubles and fixtures for exactly that: a mock that omits the changed behavior makes every test through it blind to the change, which no amount of assertion-reading reveals.

## Do not report

Coverage targets; tests for getters, wiring, or framework behavior; implementation-detail assertions; snapshot volume; one test per permutation where one representative proves the invariant; deleted behavior; missing tests for code already proved wrong (the code lens owns the defect itself).

## Severity

- **Critical gap** — an unprotected high-impact invariant (data loss, security, irreversible behavior).
- **Important gap** — meaningful supported behavior can regress silently.
- **Suggestion** — useful leverage, non-blocking. Use sparingly.

## Output

Write `$ARTIFACTS_DIR/review/tests.md`: each in-scope finding begins with `sources: [tests]`, followed by the four evidence parts and `file:line` references, then the examined-and-protected list citing the decisive assertions. In light mode, a verdict per prior finding. No findings is a valid result.

If you prove useful work outside scope.md's accepted contract, do not turn it into a blocking finding. Write `$ARTIFACTS_DIR/discoveries/review-tests.json` as a JSON array of records with `title`, `claim`, `evidence` (concrete `file:line` facts or command results), `relation` (`adjacent` or `scope_conflict`), and `source_node` (`tests`). Write no file for no discovery; never append to another lens's file or record suspicion.

Verify every cited `file:line` is real, then reply with one line pointing to it: `review findings: $ARTIFACTS_DIR/review/tests.md` and the findings count by severity.
