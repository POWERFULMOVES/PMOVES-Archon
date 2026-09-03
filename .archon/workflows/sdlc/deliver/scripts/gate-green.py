"""The green gate: run success never certifies green — this does, deterministically.

The delivery tail asks the question after implementation, after corrections, and
after the project's own full gate runs post-review. The same script answers it each
time. A node that produced a verdict is not a node that passed;
the loop completes on `done`, blocked declines included, so no spend and no public
step happens until this reads the verdict itself.

Red is not one thing, though, and treating it as one killed two correct deliveries.

A change that breaks a check must never reach a pull request. A check that
was already red at the run's starting commit, or that failed because a parallel
process held the database this run needed, is not evidence about the change at all —
and reality gets checked again downstream regardless: flip-ready refuses to make the
PR ready while its real CI is not green. So this fails on `introduced` and lets
`inherited` and `environment` through with the claim recorded where every downstream
reader meets it. An inherited base break stays red on the PR too, where the tail
pauses for explicit operator action instead of retrying or flipping the PR ready.

That trade is only safe while it stays loud, so a passed red is never silent: the
record below is what the terminal report and the pull request body repeat. A record
that cannot be written fails the gate — passing red work with no trace of why is the
one outcome worse than refusing.

`red_cause` is agent judgment. This validates the resolved value and nothing else;
the evidence behind it belongs to the declaring node's prompt and its report.

Bound inputs (`with:` bindings, canonical text in env):
- INPUTS_GREEN: the declaring node's verdict, canonical boolean text.
- INPUTS_RED_CAUSE: `introduced`, `inherited`, `environment`, or '' when the
  declared-optional field is absent.
- INPUTS_SUMMARY: that node's summary, which carries the evidence for the claim.
- INPUTS_STAGE: which gate this is, for the record a human reads later.
"""

import json
import os
import sys

PASSES_RED = ("inherited", "environment")
CAUSES = ("introduced", *PASSES_RED)


def record_red_cause(artifacts: str, cause: str, stage: str, summary: str) -> None:
    """Append this gate's decision to the run's red-cause record.

    A list, not a document: the implementation, a correction, and the project gate can
    each pass red for their own reason, and a later one must not erase an earlier. An
    unreadable existing file is replaced rather than parsed around — the alternative is
    failing a delivery over a file only this gate writes — while a failed WRITE
    propagates, because the record is the whole reason passing red is allowed.
    """
    path = os.path.join(artifacts, "red-causes.json")
    records = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if isinstance(existing, list):
            records = existing
    except (OSError, ValueError):
        records = []
    records.append({"cause": cause, "stage": stage, "summary": summary})
    os.makedirs(artifacts, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    artifacts = os.environ["ARTIFACTS_DIR"]
    green = os.environ.get("INPUTS_GREEN", "").strip()
    cause = os.environ.get("INPUTS_RED_CAUSE", "").strip()
    summary = os.environ.get("INPUTS_SUMMARY", "").strip()
    stage = os.environ.get("INPUTS_STAGE", "").strip() or "The work"

    if green == "true":
        print(json.dumps({"gate": "green"}))
        return 0

    if cause not in CAUSES:
        print(
            f"{stage} is red and declared no usable red_cause "
            f"(got '{cause}'; expected one of {', '.join(CAUSES)}). Red that nobody "
            "explained is red this gate refuses — its summary says what happened.",
            file=sys.stderr,
        )
        return 1

    if cause == "introduced":
        print(
            f"{stage} is red, and the cause is the change itself. "
            "Refusing to open or advance a pull request on red work.",
            file=sys.stderr,
        )
        return 1

    # The label is not the claim. A pass on non-introduced red is worth exactly the
    # evidence behind it — the failing check named, and why this change cannot have
    # caused it — and an empty summary carries none, so the caveat it records says
    # nothing a reader can act on. Refused for the same reason an unwritable record is:
    # red that leaves no trace of why is worse than red that stops here. Emptiness is
    # all this checks; whether the prose is genuine evidence is the declaring agent's
    # judgment and the reviewer's, never something to reconstruct from the text.
    if not summary:
        print(
            f"{stage} declared its red {cause}, but recorded no evidence for the claim. "
            "A pass on red the change did not cause is only as good as the failing check "
            "it names — refusing without it.",
            file=sys.stderr,
        )
        return 1

    try:
        record_red_cause(artifacts, cause, stage, summary)
    except OSError as err:
        print(
            f"{stage} declared '{cause}' red, but the caveat could not be recorded "
            f"({err}). Refusing to pass red work that leaves no trace of why.",
            file=sys.stderr,
        )
        return 1

    print(
        f"{stage} is red, and declared that red {cause} rather than introduced. "
        "Proceeding so the pull request's own CI can be observed; a red conclusion "
        "requires explicit operator action.",
        file=sys.stderr,
    )
    print(json.dumps({"gate": "green", "red_cause": cause}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
