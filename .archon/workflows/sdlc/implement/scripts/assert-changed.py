"""Deterministic guard: does this run have work to show?

An AI node that declines its task still exits 0, so without this check the
stages after implement would spend money or go public on nothing. It reads
Archon-owned facts only -- git state and the run's own recorded artifacts --
never the project's layout or toolchain.

Four ways to pass, in order:
1. The working tree changed since the run started (outside `.archon/`).
2. Commits were made since the recorded start SHA.
3. Verified existing work: no new change this run, but the loop declared
   green AND the branch already carries commits ahead of the base branch --
   a rerun that verified a fix a prior run committed is progress, not a
   decline.
4. An honest decline on red the change did not cause: nothing changed, the
   loop is not green, and it declared that red `inherited` or `environment`
   with evidence in its summary. A correction round can genuinely have
   nothing left to edit -- the remaining break is in the base, or in
   configuration the run has no permission to change -- and demanding a
   change anyway asks for an invented one, or throws away the rounds that
   already landed. What such a claim is worth is the green gates' question,
   not this one; the tolerance lives here only so a change that cannot exist
   stops being required.

Red the loop introduced still fails with nothing to show, and so does red it
left unexplained or unevidenced -- the same bar the green gates hold, because
a cause with no failing check named behind it is not a reason. A green claim
with neither new work nor a branch lead fails too.

Only UNCOMMITTED `.archon/` changes are excluded: Archon copies the operator's
workflow edits into every run worktree, so pre-existing uncommitted `.archon/`
files predate implement and are not its output. A commit made during the run
counts as work even when it only touches `.archon/` -- run-made commits are the
run's output (implement legitimately edits workflows).
"""

import os
import subprocess
import sys
from pathlib import Path

EXCLUDE = ":(exclude).archon"
# Red the loop can pass on without having caused it, in the same vocabulary the
# green gates route on. Keep the two in step: a cause one accepts and the other
# refuses would strand an iteration between them.
PASSES_RED = ("inherited", "environment")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def try_git(*args: str) -> str | None:
    proc = subprocess.run(["git", *args], capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else None


def main() -> int:
    artifacts = Path(os.environ["ARTIFACTS_DIR"])
    start = (artifacts / ".start-sha").read_text().strip()
    # The loop's verdict, bound by the workflow (`with:`): green as canonical
    # boolean text ("true"/"false"), the declared cause of any red, and the
    # summary that carries the evidence for it.
    green = os.environ.get("INPUTS_GREEN", "").strip()
    red_cause = os.environ.get("INPUTS_RED_CAUSE", "").strip()
    summary = os.environ.get("INPUTS_SUMMARY", "").strip()

    tracked = git("diff", "--name-only", "HEAD", "--", EXCLUDE)
    untracked = git("ls-files", "--others", "--exclude-standard", "--", EXCLUDE)
    head = git("rev-parse", "HEAD")

    if tracked or untracked:
        stat = git("diff", "--stat", "HEAD", "--", EXCLUDE)
        print(stat.splitlines()[-1] if stat else "working-tree changes present")
        return 0

    if head != start:
        count = git("rev-list", "--count", f"{start}..HEAD")
        print(f"{count} commit(s) made this run")
        return 0

    base = os.environ.get("BASE_BRANCH", "")
    if green == "true" and base:
        for ref in (f"origin/{base}", base):
            ahead = try_git("rev-list", "--count", f"{ref}..HEAD")
            if ahead is not None:
                if int(ahead) > 0:
                    print(
                        f"no new changes this run; verified existing work -- "
                        f"{ahead} commit(s) ahead of {ref}"
                    )
                    return 0
                break

    # Nothing to show, and nothing to do about it. The evidence bar is the green
    # gates' own: emptiness is all that is checked, because whether the prose names
    # a real failing check is the declaring agent's judgment and the reviewer's.
    if green != "true" and red_cause in PASSES_RED and summary:
        print(f"no new changes this run; the remaining red is declared {red_cause}, not introduced")
        return 0

    print(
        "implement produced neither a commit nor a working-tree change outside .archon/, "
        f"and the branch carries no verified work ahead of the base "
        f"(green={green or 'unknown'}, red_cause={red_cause or 'unknown'}).\n"
        "Nothing to show is only acceptable on red the change did not cause -- declared "
        f"{' or '.join(PASSES_RED)}, with the failing check named in the summary. Red the "
        "change introduced, red nobody explained, and a cause with no evidence behind it "
        "fail here rather than reporting success.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
