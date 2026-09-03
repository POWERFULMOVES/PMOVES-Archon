"""Resolve operator review-lens overrides against the classifier's judgment."""

import json
import os
import sys

LENSES = ("errors",)


def resolve(forced: str, judged: str, lens: str) -> str:
    if forced in ("true", "false"):
        return forced
    if judged not in ("true", "false"):
        print(
            f"resolve-review-scope: classifier returned an invalid {lens} verdict: {judged!r}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return judged


def main() -> int:
    resolved = {
        lens: resolve(
            os.environ.get(f"INPUTS_{lens.upper()}", ""),
            os.environ.get(f"INPUTS_C_{lens.upper()}", ""),
            lens,
        )
        for lens in LENSES
    }
    print(json.dumps(resolved, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
