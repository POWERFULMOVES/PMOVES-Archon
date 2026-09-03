"""Carry a validated late-CI review verdict and its red classification out of the loop."""

import json
import os
import sys


def main() -> int:
    ready = os.environ.get("INPUTS_READY", "")
    action = os.environ.get("INPUTS_ACTION", "")
    red_cause = os.environ.get("INPUTS_RED_CAUSE", "").strip()

    valid_verdict = (ready == "true" and action == "none") or (
        ready == "false" and action in ("correct", "replan")
    )
    if not valid_verdict:
        print(
            "invalid late-CI review verdict: expected ready=true/action=none or "
            f"ready=false/action=correct|replan, got ready={ready!r} action={action!r}",
            file=sys.stderr,
        )
        return 1
    if red_cause not in ("", "introduced", "inherited", "environment"):
        print(f"invalid late-CI red cause: {red_cause!r}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {"ready": ready == "true", "action": action, "red_cause": red_cause},
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
