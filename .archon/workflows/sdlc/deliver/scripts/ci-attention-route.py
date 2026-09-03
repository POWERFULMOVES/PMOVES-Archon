"""Route non-introduced late CI red to an explicit operator action."""

import json
import os
import sys


def main() -> int:
    red_cause = os.environ.get("INPUTS_RED_CAUSE", "").strip()
    if red_cause not in ("", "introduced", "inherited", "environment"):
        print(f"invalid late-CI red cause: {red_cause!r}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "attention": red_cause in ("inherited", "environment"),
                "red_cause": red_cause,
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
