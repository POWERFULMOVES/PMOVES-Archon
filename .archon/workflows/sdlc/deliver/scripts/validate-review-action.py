"""Validate the review verdict before it controls delivery."""

import json
import os
import sys


def main() -> int:
    ready = os.environ.get("INPUTS_READY", "")
    action = os.environ.get("INPUTS_ACTION", "")

    valid = (ready == "true" and action == "none") or (
        ready == "false" and action in ("correct", "replan")
    )
    if not valid:
        print(
            "invalid review verdict: expected ready=true/action=none or "
            f"ready=false/action=correct|replan, got ready={ready!r} action={action!r}",
            file=sys.stderr,
        )
        return 1

    print(json.dumps({"ready": ready == "true", "action": action}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
